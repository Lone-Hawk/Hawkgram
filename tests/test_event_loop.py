#  Hawkgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2026-present Lone Hawk <https://github.com/Lone-Hawk>
#
#  This file is part of Hawkgram.
#
#  Hawkgram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Hawkgram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Hawkgram.  If not, see <http://www.gnu.org/licenses/>.

"""Event loop handling: since Python 3.14 asyncio.get_event_loop() raises instead of creating a loop.

Every test runs in a new thread, which starts without a current event loop (like the main thread after
asyncio.run() has returned), so no loop leaks into or out of the other tests.
"""

import asyncio
import threading

import pytest

import pyrogram
from pyrogram import utils
from pyrogram.handlers import MessageHandler
from pyrogram.methods.auth import connect as connect_module


def in_new_thread(func):
    result = {}

    def target():
        try:
            result["value"] = func()
        except BaseException as e:
            result["error"] = e
        finally:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None

            if loop is not None and not loop.is_closed():
                loop.close()

            asyncio.set_event_loop(None)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()

    if "error" in result:
        raise result["error"]

    return result.get("value")


def new_client(tmp_path):
    return pyrogram.Client("loop", api_id=1, api_hash="0" * 32, in_memory=True, workdir=str(tmp_path))


async def noop():
    pass


def test_get_event_loop_creates_a_loop_when_none_is_set():
    def check():
        asyncio.run(noop())  # leaves no current event loop behind

        loop = utils.get_event_loop()

        assert not loop.is_closed()
        assert asyncio.get_event_loop() is loop
        assert utils.get_event_loop() is loop

    in_new_thread(check)


def test_get_event_loop_replaces_a_closed_loop():
    def check():
        closed = asyncio.new_event_loop()
        asyncio.set_event_loop(closed)
        closed.close()

        loop = utils.get_event_loop()

        assert loop is not closed and not loop.is_closed()

    in_new_thread(check)


def test_get_event_loop_returns_the_running_loop():
    async def main():
        return utils.get_event_loop() is asyncio.get_running_loop()

    assert in_new_thread(lambda: asyncio.run(main()))


def test_client_can_be_created_without_a_current_loop(tmp_path):
    def check():
        asyncio.run(noop())
        app = new_client(tmp_path)

        assert not app.loop.is_closed()
        assert app.dispatcher.loop is app.loop

    in_new_thread(check)


def test_run_works_after_asyncio_run(tmp_path):
    ran = []

    async def main():
        ran.append(True)

    def check():
        app = new_client(tmp_path)
        initial_loop = app.loop

        try:
            asyncio.run(noop())  # resets the current loop to None
            app.run(main())
        finally:
            initial_loop.close()

    in_new_thread(check)

    assert ran == [True]


def test_handlers_added_without_a_running_loop_are_registered_at_once(tmp_path):
    def check():
        app = new_client(tmp_path)
        builtin = list(app.dispatcher.groups[0])  # pyromod's conversation handler

        @app.on_message()
        async def handler(_, __):
            pass

        # Previously a task was scheduled on the loop captured at construction: with asyncio.run that loop never
        # runs, so the handler was never registered
        assert len(app.dispatcher.groups[0]) == len(builtin) + 1
        added = app.dispatcher.groups[0][-1]
        assert isinstance(added, MessageHandler) and added.original_callback is handler

        app.remove_handler(added, 0)
        assert app.dispatcher.groups[0] == builtin

        with pytest.raises(ValueError):
            app.remove_handler(MessageHandler(handler), 1)

    in_new_thread(check)


def test_handlers_added_inside_a_running_loop_wait_for_the_workers(tmp_path):
    async def main(app):
        await app.dispatcher.start()

        try:
            handler = MessageHandler(noop)
            app.add_handler(handler)
            await asyncio.sleep(0)

            return handler in app.dispatcher.groups[0]
        finally:
            await app.dispatcher.stop()

    def check():
        app = new_client(tmp_path)
        initial_loop = app.loop

        try:
            return asyncio.run(main(app))
        finally:
            initial_loop.close()

    assert in_new_thread(check)


def test_handlers_added_from_another_thread_go_through_the_client_loop(tmp_path):
    async def main(app):
        await app.dispatcher.start()

        try:
            handler = MessageHandler(noop)
            lock = app.dispatcher.locks_list[0]

            # A thread without a running loop (e.g. using the sync methods) while the client is running and a
            # worker holds its lock: the change waits for the lock instead of happening under the worker's feet
            async with lock:
                thread = threading.Thread(target=app.add_handler, args=(handler,))
                thread.start()
                await asyncio.get_running_loop().run_in_executor(None, thread.join)
                await asyncio.sleep(0.1)

                assert handler not in app.dispatcher.groups[0]

            await asyncio.sleep(0.1)

            return handler in app.dispatcher.groups[0]
        finally:
            await app.dispatcher.stop()

    def check():
        app = new_client(tmp_path)
        initial_loop = app.loop

        try:
            return asyncio.run(main(app))
        finally:
            initial_loop.close()

    assert in_new_thread(check)


def test_module_level_client_runs_on_the_asyncio_run_loop(tmp_path, monkeypatch):
    class FakeStorage:
        async def dc_id(self):
            return 2

        async def auth_key(self):
            return bytes(256)

        async def test_mode(self):
            return False

        async def user_id(self):
            return 1

    class FakeSession:
        def __init__(self, *args, **kwargs):
            pass

        async def start(self):
            pass

    monkeypatch.setattr(connect_module, "Session", FakeSession)

    def check():
        # Created outside of any running loop, like a client defined at module level
        app = new_client(tmp_path)
        app.storage = FakeStorage()

        async def load_session():
            pass

        app.load_session = load_session

        async def main():
            running = asyncio.get_running_loop()

            assert running is not app.loop
            assert await app.connect() is True
            assert app.loop is running

            await app.dispatcher.start()

            try:
                assert app.dispatcher.loop is running
                assert all(task.get_loop() is running for task in app.dispatcher.handler_worker_tasks)
            finally:
                await app.dispatcher.stop()

        initial_loop = app.loop

        try:
            asyncio.run(main())
        finally:
            initial_loop.close()

    in_new_thread(check)
