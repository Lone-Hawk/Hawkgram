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

"""SQLite session storage: what is written and when it is committed"""

import asyncio
import sqlite3

import pytest

from pyrogram.storage import FileStorage
from pyrogram.storage.sqlite_storage import UNAME_SCHEMA


async def open_storage(tmp_path, commit_delay=0.2):
    storage = FileStorage("account", tmp_path)
    storage.COMMIT_DELAY = commit_delay
    await storage.open()

    return storage


def committed(tmp_path, query):
    """What another connection sees: only data that has been committed to the file"""
    reader = sqlite3.connect(str(tmp_path / "account.session"))

    try:
        return reader.execute(query).fetchall()
    finally:
        reader.close()


async def write_updates(storage, count):
    for pts in range(1, count + 1):
        await storage.update_peers([(pts, pts * 10, "user", f"user{pts}", None)])
        await storage.update_usernames([(pts, f"alias{pts}")])
        await storage.update_state((0, pts, None, 1, None))


@pytest.mark.asyncio
async def test_updates_are_committed_together(tmp_path):
    storage = await open_storage(tmp_path)

    # The usernames table is ensured (and committed) once, on first use
    await storage.update_usernames([])
    await storage.save()

    statements = []
    storage.conn.set_trace_callback(statements.append)

    await write_updates(storage, 100)

    # Each update used to be committed (and synced to disk) on its own, several times
    assert statements.count("COMMIT") == 0
    assert committed(tmp_path, "SELECT pts FROM update_state") == []

    await asyncio.sleep(0.4)

    assert statements.count("COMMIT") == 1
    assert committed(tmp_path, "SELECT pts FROM update_state") == [(100,)]
    assert len(committed(tmp_path, "SELECT id FROM peers")) == 100
    assert len(committed(tmp_path, "SELECT id FROM usernames")) == 100

    await storage.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("finish", ["save", "close"])
async def test_pending_changes_are_committed_on_save_and_close(tmp_path, finish):
    storage = await open_storage(tmp_path, commit_delay=60)

    await write_updates(storage, 3)
    await getattr(storage, finish)()

    assert committed(tmp_path, "SELECT pts FROM update_state") == [(3,)]
    assert len(committed(tmp_path, "SELECT id FROM peers")) == 3

    if finish == "save":
        # The delayed commit was cancelled with the save
        assert storage._commit_handle is None
        await storage.close()


@pytest.mark.asyncio
async def test_removed_states_are_committed(tmp_path):
    storage = await open_storage(tmp_path)

    await storage.update_state((-1001, 5, None, 1, None))
    await storage.update_state((-1002, 6, None, 1, None))
    await storage.save()

    await storage.update_state(-1001)
    await storage.remove_state(-1002)
    await asyncio.sleep(0.4)

    assert committed(tmp_path, "SELECT id FROM update_state") == []

    await storage.close()


@pytest.mark.asyncio
async def test_usernames_replace_the_previous_ones_of_a_peer(tmp_path):
    storage = await open_storage(tmp_path)

    await storage.update_usernames([(1, "first"), (1, "second"), (2, "other")])
    await storage.update_usernames([(1, "third")])

    assert storage.conn.execute("SELECT id, peer_id FROM usernames ORDER BY id").fetchall() == [
        ("other", 2), ("third", 1)
    ]

    await storage.close()


@pytest.mark.asyncio
async def test_usernames_table_is_created_for_older_session_files(tmp_path):
    storage = await open_storage(tmp_path)
    storage.conn.execute("DROP TABLE usernames")
    storage.conn.commit()
    await storage.close()

    storage = await open_storage(tmp_path)
    await storage.update_usernames([(1, "alias")])
    await storage.update_usernames([(1, "alias2")])

    assert storage.conn.execute("SELECT id FROM usernames").fetchall() == [("alias2",)]
    assert "usernames" in UNAME_SCHEMA

    await storage.close()


def test_commit_scheduled_on_a_closed_loop_does_not_block_later_commits(tmp_path):
    async def write(storage):
        await storage.update_state((0, 1, None, 1, None))

    storage = FileStorage("account", tmp_path)
    storage.COMMIT_DELAY = 0.1

    loop = asyncio.new_event_loop()
    loop.run_until_complete(storage.open())
    loop.run_until_complete(write(storage))
    loop.close()

    async def later():
        await storage.update_state((0, 2, None, 1, None))
        await asyncio.sleep(0.3)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(later())
        assert committed(tmp_path, "SELECT pts FROM update_state") == [(2,)]
        loop.run_until_complete(storage.close())
    finally:
        loop.close()


# ---------------------------------------------------------------------------------------------------------------
# MongoDB storage
# ---------------------------------------------------------------------------------------------------------------

class FakeCollection:
    """The async collection methods MongoStorage.delete() may use (like Motor/async_pymongo, no remove())"""

    def __init__(self, documents, fail=False):
        self.documents = documents
        self.fail = fail

    async def delete_one(self, query):
        if self.fail:
            raise ConnectionError("database unreachable")
        self.documents[:] = [d for d in self.documents if d["_id"] != query["_id"]]

    async def delete_many(self, query):
        assert query == {}
        self.documents.clear()


def mongo_storage(remove_peers, fail=False):
    pytest.importorskip("pymongo")
    from pyrogram.storage.mongo_storage import MongoStorage

    storage = MongoStorage.__new__(MongoStorage)
    storage._session = FakeCollection([{"_id": 0, "auth_key": b"key"}], fail=fail)
    storage._states = FakeCollection([{"_id": 0, "pts": 1}])
    storage._peer = FakeCollection([{"_id": 1}])
    storage._usernames = FakeCollection([{"_id": "alias", "peer_id": 1}])
    storage._remove_peers = remove_peers

    return storage


@pytest.mark.asyncio
async def test_mongo_delete_removes_the_peers_when_asked():
    # remove() doesn't exist in current drivers: the AttributeError was swallowed and the peers were kept
    storage = mongo_storage(remove_peers=True)

    await storage.delete()

    assert storage._session.documents == [] and storage._states.documents == []
    assert storage._peer.documents == [] and storage._usernames.documents == []


@pytest.mark.asyncio
async def test_mongo_delete_keeps_the_peers_by_default():
    storage = mongo_storage(remove_peers=False)

    await storage.delete()

    assert storage._session.documents == [] and storage._states.documents == []
    assert storage._peer.documents == [{"_id": 1}]


@pytest.mark.asyncio
async def test_mongo_delete_failures_are_raised():
    storage = mongo_storage(remove_peers=True, fail=True)

    # log_out() used to report success while the session stayed in the database
    with pytest.raises(ConnectionError):
        await storage.delete()

    assert storage._session.documents != []
