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

"""Regression tests for Message.ask and wait_for_message: who may answer, and several waits in one chat"""

import asyncio

import pytest
import pytest_asyncio

from pyrogram import enums, types
from .test_layer_229 import FakeClient

GROUP_ID = -1001234
ASKER_ID = 11
OTHER_ID = 22


@pytest_asyncio.fixture
async def client():
    client = FakeClient()
    # Futures are created on the client's loop, which must be the one the test runs on
    client.loop = asyncio.get_running_loop()

    client.sent = []

    async def send_message(**kwargs):
        client.sent.append(kwargs)
        return types.Message(id=100, chat=group(), outgoing=True)

    client.send_message = send_message

    return client


def group():
    return types.Chat(id=GROUP_ID, type=enums.ChatType.SUPERGROUP)


def group_message(client, user_id, message_id, outgoing=False):
    return types.Message(
        id=message_id, chat=group(), from_user=types.User(id=user_id), outgoing=outgoing, text="text", client=client
    )


async def deliver(client, message):
    """Give a new message to the conversation handler, like the dispatcher does; True if it was someone's answer"""
    answered = await client.dispatcher.conversation_handler.check(client, message)

    # Let the waiting task take its answer
    await asyncio.sleep(0)

    return answered


async def started(coroutine):
    task = asyncio.create_task(coroutine)

    # Let it send its question and start waiting
    for _ in range(3):
        await asyncio.sleep(0)

    return task


@pytest.mark.asyncio
async def test_ask_takes_only_the_askers_answer(client):
    question = group_message(client, ASKER_ID, 1)
    task = await started(question.ask("Your name?", timeout=5))

    # Anyone else's message in the group used to be taken as the asker's answer
    assert not await deliver(client, group_message(client, OTHER_ID, 2))
    assert not task.done()

    assert await deliver(client, group_message(client, ASKER_ID, 3))
    answer = await task

    assert answer.id == 3 and answer.request.id == 100
    assert client.dispatcher.conversation_handler.waiters == {}


@pytest.mark.asyncio
async def test_ask_on_an_own_message_takes_anyones_answer(client):
    question = group_message(client, 99, 1, outgoing=True)
    task = await started(question.ask("Anyone?", timeout=5))

    assert await deliver(client, group_message(client, OTHER_ID, 2))
    assert (await task).id == 2


@pytest.mark.asyncio
async def test_two_asks_in_one_chat_each_get_their_answer(client):
    first = await started(group_message(client, ASKER_ID, 1).ask("First?", timeout=5))
    second = await started(group_message(client, OTHER_ID, 2).ask("Second?", timeout=5))

    # The second wait used to replace the first, which then never got an answer
    assert await deliver(client, group_message(client, OTHER_ID, 3))
    assert await deliver(client, group_message(client, ASKER_ID, 4))

    assert (await first).id == 4
    assert (await second).id == 3
    assert client.dispatcher.conversation_handler.waiters == {}


@pytest.mark.asyncio
async def test_waits_without_a_user_are_answered_in_order(client):
    first = await started(client.wait_for_message(GROUP_ID, timeout=5))
    second = await started(client.wait_for_message(GROUP_ID, timeout=5))

    assert await deliver(client, group_message(client, OTHER_ID, 1))
    assert await deliver(client, group_message(client, ASKER_ID, 2))
    assert not await deliver(client, group_message(client, ASKER_ID, 3))

    assert ((await first).id, (await second).id) == (1, 2)


@pytest.mark.asyncio
async def test_a_wait_that_times_out_leaves_the_others(client):
    waiting = await started(client.wait_for_message(GROUP_ID, user_id=ASKER_ID, timeout=5))

    with pytest.raises(asyncio.TimeoutError):
        await client.wait_for_message(GROUP_ID, user_id=OTHER_ID, timeout=0.01)

    assert await deliver(client, group_message(client, ASKER_ID, 1))
    assert (await waiting).id == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("chat_type, quoted", [
    # Compared with the string "private", the chat type never matched: private chats were quoted too
    (enums.ChatType.PRIVATE, False),
    (enums.ChatType.SUPERGROUP, True),
], ids=["private", "group"])
async def test_ask_quotes_by_default_only_in_groups(client, chat_type, quoted):
    question = types.Message(
        id=7, chat=types.Chat(id=ASKER_ID, type=chat_type), from_user=types.User(id=ASKER_ID), client=client
    )

    with pytest.raises(asyncio.TimeoutError):
        await question.ask("Your name?", timeout=0.01)

    (sent,) = client.sent
    assert sent["reply_to_message_id"] == (7 if quoted else None)
