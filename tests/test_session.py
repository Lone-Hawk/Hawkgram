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

import asyncio
import os
import time
from types import SimpleNamespace

import pytest

from pyrogram import raw
from pyrogram.errors import BadMsgNotification, FloodWait, InternalServerError, ServiceUnavailable
from pyrogram.raw.core import Message
from pyrogram.session import Session
from pyrogram.session.internals import MsgId
from pyrogram.session.session import Result

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


# ---------------------------------------------------------------------------------------------------------------
# Payments are never sent again when it isn't known whether they went through
# ---------------------------------------------------------------------------------------------------------------

class SilentConnection:
    """Takes every request and never answers, like a connection lost after the request went out"""

    def __init__(self):
        self.sent = 0

    async def send(self, payload):
        self.sent += 1


def silent_session():
    session = make_session([])
    session.connection = SilentConnection()
    session.client = SimpleNamespace(name="test")
    session.is_started.set()

    return session


def send_stars_form():
    return raw.functions.payments.SendStarsForm(form_id=1, invoice=T.InputInvoiceSlug(slug="slug"))


payment_requests = pytest.mark.parametrize("query", [
    send_stars_form(),
    raw.functions.InvokeWithoutUpdates(query=send_stars_form()),
    raw.functions.InvokeWithBusinessConnection(connection_id="connection", query=send_stars_form()),
    raw.functions.payments.RefundStarsCharge(user_id=T.InputUserSelf(), charge_id="charge"),
], ids=["send-stars-form", "without-updates", "business-connection", "refund"])


@pytest.mark.asyncio
@payment_requests
async def test_payments_are_not_sent_again_after_a_timeout(query):
    session = silent_session()

    # The payment may have gone through although its answer didn't come: it used to be sent 11 times
    with pytest.raises(TimeoutError, match="was not sent again"):
        await session.invoke(query, timeout=0.01)

    assert session.connection.sent == 1
    assert session.results == {}


@pytest.mark.asyncio
@payment_requests
@pytest.mark.parametrize("error", [
    InternalServerError(), ServiceUnavailable(), OSError("connection reset")
], ids=["internal-server-error", "service-unavailable", "connection-lost"])
async def test_payments_are_not_sent_again_after_an_error(query, error):
    session = silent_session()
    sent = []

    async def send(query, *args, **kwargs):
        sent.append(query)
        raise error

    session.send = send

    with pytest.raises(type(error)):
        await session.invoke(query)

    assert sent == [query]


@pytest.mark.asyncio
async def test_other_requests_are_still_sent_again_after_a_timeout(monkeypatch):
    session = silent_session()
    sleep = asyncio.sleep
    monkeypatch.setattr("pyrogram.session.session.asyncio.sleep", lambda delay: sleep(0))

    with pytest.raises(TimeoutError, match="Request timed out"):
        await session.invoke(raw.functions.Ping(ping_id=1), retries=2, timeout=0.01)

    assert session.connection.sent == 3


# ---------------------------------------------------------------------------------------------------------------
# A client clock that is off
# ---------------------------------------------------------------------------------------------------------------

SKEW = 3600  # The server's clock is an hour ahead of the local one


class SkewedServer:
    """Hands messages to Session.handle_packet as if decrypted from the server, whose msg_ids carry its time"""

    def __init__(self, session, monkeypatch, skew=SKEW):
        self.session = session
        self.skew = skew
        self.counter = 0
        self.closed = False
        self.sent_msg_ids = []
        self.next_message = None

        monkeypatch.setattr("pyrogram.session.session.mtproto.unpack", lambda *args: self.next_message)

    def server_msg_id(self):
        self.counter += 4
        return int(time.time() + self.skew) * 2 ** 32 + self.counter + 1

    async def deliver(self, body):
        self.next_message = Message(body, self.server_msg_id(), 0, 0)
        await self.session.handle_packet(b"")

    async def close(self):
        self.closed = True


@pytest.fixture
def local_clock(monkeypatch):
    """The process-wide MsgId state, restored after the test"""
    monkeypatch.setattr(MsgId, "server_time_offset", 0)
    monkeypatch.setattr(MsgId, "last_time", 0)
    monkeypatch.setattr(MsgId, "offset", 0)


def server_time_of(msg_id):
    return msg_id / 2 ** 32


@pytest.mark.asyncio
@pytest.mark.parametrize("skew, error_code", [(SKEW, 16), (-SKEW, 17)], ids=["clock-behind", "clock-ahead"])
async def test_requests_work_with_a_client_clock_that_is_off(monkeypatch, local_clock, skew, error_code):
    session = make_session([])
    server = SkewedServer(session, monkeypatch, skew)

    class Connection:
        async def send(self, payload):
            (msg_id,) = session.results
            server.sent_msg_ids.append(msg_id)

            if abs(server_time_of(msg_id) - (time.time() + skew)) > 30:
                # Telegram rejects a msg_id too far from its own time
                await server.deliver(T.BadMsgNotification(bad_msg_id=msg_id, bad_msg_seqno=0, error_code=error_code))
            else:
                await server.deliver(T.RpcResult(req_msg_id=msg_id, result=T.Pong(msg_id=msg_id, ping_id=1)))

        close = server.close

    session.connection = Connection()

    # The server's answers fell outside the msg_id time window, so they were all dropped and the connection closed
    result = await session.send(raw.functions.Ping(ping_id=1), timeout=1)

    assert isinstance(result, T.Pong)
    assert not server.closed
    first, retry = server.sent_msg_ids
    assert abs(server_time_of(retry) - (time.time() + skew)) < 5
    assert abs(MsgId.server_time_offset - skew) < 5


@pytest.mark.asyncio
async def test_unsolicited_bad_msg_notification_does_not_change_the_clock(monkeypatch, local_clock):
    # Only a notification answering a request that is waiting may set the time: an old one replayed after
    # reconnecting must not
    session = make_session([])
    server = SkewedServer(session, monkeypatch)
    session.connection = server

    await server.deliver(T.BadMsgNotification(bad_msg_id=12345 * 2 ** 32, bad_msg_seqno=0, error_code=16))

    assert server.closed
    assert MsgId.server_time_offset == 0


@pytest.mark.asyncio
async def test_messages_outside_the_time_window_are_still_dropped(monkeypatch, local_clock):
    session = make_session([])
    server = SkewedServer(session, monkeypatch)
    session.connection = server
    session.results[MsgId()] = Result()

    await server.deliver(T.Pong(msg_id=0, ping_id=1))

    assert server.closed
