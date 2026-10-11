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

"""Session.send: answers that make the request be sent again"""

import os
from types import SimpleNamespace

import pytest

from pyrogram import raw
from pyrogram.errors import BadMsgNotification, FloodWait
from pyrogram.session import Session

T = raw.types


class FakeConnection:
    """Answers each request sent by the session with the next answer, like the recv worker would"""

    def __init__(self, session, answers):
        self.session = session
        self.answers = list(answers)
        self.sent_msg_ids = []

    async def send(self, payload):
        # Only the request being sent is waiting for its result
        (msg_id,) = self.session.results
        self.sent_msg_ids.append(msg_id)

        self.session.results[msg_id].value = self.answers.pop(0)
        self.session.results[msg_id].event.set()


def make_session(answers):
    session = Session(client=None, dc_id=2, auth_key=os.urandom(256), test_mode=False)
    session.connection = FakeConnection(session, answers)

    return session


def bad_msg_notification(error_code=16):
    return T.BadMsgNotification(bad_msg_id=0, bad_msg_seqno=0, error_code=error_code)


@pytest.mark.asyncio
async def test_bad_msg_notification_returns_the_result_of_the_retry():
    pong = T.Pong(msg_id=0, ping_id=1)
    session = make_session([bad_msg_notification(), pong])

    # The notification itself used to be returned as the answer (and with no stored msg_ids, IndexError was raised)
    assert await session.send(raw.functions.Ping(ping_id=1)) is pong

    # The request was sent again as a new message
    first, second = session.connection.sent_msg_ids
    assert second != first
    assert session.results == {}


@pytest.mark.asyncio
async def test_bad_msg_notification_does_not_touch_the_received_msg_ids():
    session = make_session([bad_msg_notification(), T.Pong(msg_id=0, ping_id=1)])
    session.stored_msg_ids = [100, 104, 108]

    await session.send(raw.functions.Ping(ping_id=1))

    # These are the server's msg_ids, used to reject replayed messages: they must stay as received
    assert session.stored_msg_ids == [100, 104, 108]


@pytest.mark.asyncio
async def test_repeated_bad_msg_notifications_are_raised():
    session = make_session([bad_msg_notification(17)] * 3)

    with pytest.raises(BadMsgNotification, match=r"\[17\]"):
        await session.send(raw.functions.Ping(ping_id=1))

    assert len(session.connection.sent_msg_ids) == 3
    assert session.results == {}


@pytest.mark.asyncio
async def test_retries_keep_the_callers_sleep_threshold():
    session = make_session([])
    session.client = SimpleNamespace(name="test")
    session.is_started.set()
    answers = [OSError("connection reset"), FloodWait(value=1), T.Pong(msg_id=0, ping_id=1)]

    async def send(query, *args, **kwargs):
        answer = answers.pop(0)

        if isinstance(answer, Exception):
            raise answer

        return answer

    session.send = send

    # sleep_threshold=0 means "never wait for a flood wait": the retry after the network error used to wait anyway,
    # with the default threshold
    with pytest.raises(FloodWait):
        await session.invoke(raw.functions.Ping(ping_id=1), sleep_threshold=0)

    assert len(answers) == 1
