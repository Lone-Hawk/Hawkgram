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

"""Regression tests for Client methods, with requests and answers going through FakeClient"""

import pytest

from pyrogram import raw
from .test_layer_229 import FakeClient, USER_ID, CHANNEL_ID, CHANNEL_RAW_ID

T = raw.types

GROUP_RAW_ID = 77
OTHER_USER_ID = 3


@pytest.fixture
def client():
    return FakeClient()


def message(message_id, peer):
    return T.Message(id=message_id, peer_id=peer, date=1, message="text")


def found(*messages):
    return T.messages.Messages(messages=list(messages), topics=[], chats=[], users=[])


# ---------------------------------------------------------------------------------------------------------------
# delete_messages only deletes messages of the given chat
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("chat_id, own_peer", [
    (USER_ID, T.PeerUser(user_id=USER_ID)),
    (-GROUP_RAW_ID, T.PeerChat(chat_id=GROUP_RAW_ID)),
])
async def test_delete_messages_skips_messages_of_other_chats(client, chat_id, own_peer):
    # Private chats and basic groups share message ids: id 6 is in another chat, id 7 doesn't exist
    client.responses = [
        found(
            message(5, own_peer),
            message(6, T.PeerChat(chat_id=GROUP_RAW_ID + 1)),
            T.MessageEmpty(id=7),
            message(8, own_peer),
        ),
        T.messages.AffectedMessages(pts=10, pts_count=2),
    ]

    assert await client.delete_messages(chat_id, [5, 6, 7, 8], revoke=False) == 2

    get_messages, delete = client.requests
    assert get_messages.id == [T.InputMessageID(id=i) for i in (5, 6, 7, 8)]
    assert isinstance(delete, raw.functions.messages.DeleteMessages)
    assert delete.id == [5, 8]
    assert not delete.revoke


@pytest.mark.asyncio
async def test_delete_messages_deletes_nothing_when_no_message_is_in_the_chat(client):
    # A bot asked to delete message 6 "in chat USER_ID" must not delete it from another chat
    client.responses = [found(message(6, T.PeerUser(user_id=OTHER_USER_ID)))]

    assert await client.delete_messages(USER_ID, 6) == 0
    assert len(client.requests) == 1


@pytest.mark.asyncio
async def test_delete_messages_in_saved_messages(client):
    await client.storage.open()
    await client.storage.user_id(USER_ID)

    client.responses = [
        found(message(5, T.PeerUser(user_id=USER_ID)), message(6, T.PeerUser(user_id=OTHER_USER_ID))),
        T.messages.AffectedMessages(pts=10, pts_count=1),
    ]

    assert await client.delete_messages("me", [5, 6]) == 1
    assert client.requests[1].id == [5]


@pytest.mark.asyncio
async def test_delete_messages_in_channels_names_the_channel(client):
    client.responses = [T.messages.AffectedMessages(pts=10, pts_count=2)]

    assert await client.delete_messages(CHANNEL_ID, [5, 6]) == 2

    (delete,) = client.requests
    assert isinstance(delete, raw.functions.channels.DeleteMessages)
    assert delete.channel == T.InputPeerChannel(channel_id=CHANNEL_RAW_ID, access_hash=9)
    assert delete.id == [5, 6]
