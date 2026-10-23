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

"""Each session sends and processes its messages in order, also when they are encrypted in several threads at once"""

import asyncio
import itertools
from concurrent.futures import ThreadPoolExecutor
import os
import threading
import time
from io import BytesIO
from types import SimpleNamespace

import pytest

import pyrogram
from pyrogram import raw
from pyrogram.connection.transport.tcp import tcp_abridged_o
from pyrogram.connection.transport.tcp.tcp_abridged_o import TCPAbridgedO
from pyrogram.crypto import aes
from pyrogram.raw.core import Message
from pyrogram.session import Session
from pyrogram.session.internals import Sequencer

T = raw.types


@pytest.fixture
def four_crypto_threads(monkeypatch):
    """Encrypt and decrypt in 4 threads during a test. The pool has one thread, which happens to keep calls in order,
    but pyrogram.crypto_executor can be replaced by any executor: the order must not depend on it"""
    executor = ThreadPoolExecutor(4)
    monkeypatch.setattr(pyrogram, "crypto_executor", executor)
    yield
    executor.shutdown(wait=True)


def slow_in_reverse(func, count, step=0.02):
    """Wrap a function so that, of *count* calls made at once, the first finishes last"""
    calls = itertools.count()
    finished = []

    def wrapper(*args):
        n = next(calls)
        time.sleep((count - n) * step)
        finished.append(n)
        return func(*args)

    wrapper.finished = finished
    return wrapper


# ---------------------------------------------------------------------------------------------------------------
# Sequencer
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sequencer_keeps_the_order_the_turns_were_taken():
    sequencer = Sequencer()
    order = []

    async def work(i, delay):
        turn = sequencer.take()

        try:
            await asyncio.sleep(delay)
            await turn.wait()
            order.append(i)
        finally:
            turn.done()

    await asyncio.gather(*(work(i, (5 - i) * 0.01) for i in range(5)))

    assert order == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_cancelled_turn_neither_blocks_nor_skips_the_queue():
    sequencer = Sequencer()
    order = []
    release_first = asyncio.Event()

    async def work(i, event=None):
        turn = sequencer.take()

        try:
            if event is not None:
                await event.wait()
            await turn.wait()
            order.append(i)
        finally:
            turn.done()

    first = asyncio.create_task(work(0, release_first))
    second = asyncio.create_task(work(1, asyncio.Event()))  # never released: cancelled below
    third = asyncio.create_task(work(2))
    await asyncio.sleep(0.01)

    second.cancel()
    await asyncio.sleep(0.01)
    # The cancelled turn ends only once the turn before it is done
    assert order == [] and not third.done()

    release_first.set()
    await asyncio.wait_for(asyncio.gather(first, third), 5)

    assert order == [0, 2]


# ---------------------------------------------------------------------------------------------------------------
# Sessions with more than one crypto thread
# ---------------------------------------------------------------------------------------------------------------

def make_session():
    return Session(client=None, dc_id=2, auth_key=os.urandom(256), test_mode=False)


@pytest.mark.asyncio
async def test_messages_are_sent_in_msg_id_order(four_crypto_threads, monkeypatch):
    count = 6
    pack = slow_in_reverse(lambda message, *args: message.msg_id.to_bytes(8, "little"), count)
    monkeypatch.setattr("pyrogram.session.session.mtproto.pack", pack)
    session = make_session()
    sent = []

    class Connection:
        async def send(self, payload):
            await asyncio.sleep(0)
            sent.append(int.from_bytes(payload, "little"))

    session.connection = Connection()

    await asyncio.gather(*(session.send(raw.functions.Ping(ping_id=i), wait_response=False) for i in range(count)))

    # Encrypted in parallel, finishing in reverse order...
    assert pack.finished != sorted(pack.finished)
    # ...but sent in msg_id order: Telegram rejects a msg_id or seq_no lower than one it has received
    assert len(sent) == count and sent == sorted(sent)


@pytest.mark.asyncio
async def test_packets_are_processed_in_the_order_they_arrived(four_crypto_threads, monkeypatch):
    count = 6
    base = int(time.time()) * 2 ** 32

    def unpack(b: BytesIO, *args):
        i = b.read()[0]
        return Message(T.Pong(msg_id=i, ping_id=0), base + 4 * (i + 1) + 1, 0, 0)

    unpack = slow_in_reverse(unpack, count)
    monkeypatch.setattr("pyrogram.session.session.mtproto.unpack", unpack)
    session = make_session()
    processed = []
    closed = []

    class Connection:
        async def close(self):
            closed.append(True)

    session.connection = Connection()

    for i in range(count):
        session.results[i] = SimpleNamespace(value=None, event=SimpleNamespace(set=lambda i=i: processed.append(i)))

    # recv_worker starts one task per packet, in the order they arrive
    tasks = [asyncio.create_task(session.handle_packet(bytes([i]))) for i in range(count)]
    await asyncio.gather(*tasks)

    assert unpack.finished != sorted(unpack.finished)
    # Processed out of order, a packet found a later msg_id already stored: it was dropped and the connection closed
    assert processed == list(range(count))
    assert not closed


class FakeWriter:
    def __init__(self):
        self.data = bytearray()

    def write(self, data):
        self.data += data

    async def drain(self):
        await asyncio.sleep(0)


def obfuscated_transport():
    transport = TCPAbridgedO(ipv6=False, proxy=None)
    key, iv = os.urandom(32), bytearray(os.urandom(16))
    transport.encrypt = (key, iv, bytearray(1))
    transport.writer = FakeWriter()

    return transport, (key, bytearray(iv), bytearray(1))


def read_frames(stream: bytes, decrypt) -> list:
    """Decrypt an abridged obfuscated stream from its start and split it into its payloads"""
    plain = aes.ctr256_decrypt(stream, *decrypt)
    frames = []

    while plain:
        length, plain = plain[0], plain[1:]

        if length == 0x7f:
            length, plain = int.from_bytes(plain[:3], "little"), plain[3:]

        frames.append(plain[:length * 4])
        plain = plain[length * 4:]

    return frames


@pytest.mark.asyncio
async def test_obfuscated_transport_encrypts_payloads_in_the_order_they_are_written(four_crypto_threads, monkeypatch):
    count = 6
    encrypt = slow_in_reverse(aes.ctr256_encrypt, count, step=0.01)
    monkeypatch.setattr(tcp_abridged_o.aes, "ctr256_encrypt", encrypt)
    transport, decrypt = obfuscated_transport()
    payloads = [os.urandom(4 * (i + 1) * 40) for i in range(count)]

    # Two payloads encrypted at once both start from the same CTR state: the stream can't be decrypted
    await asyncio.gather(*(transport.send(p) for p in payloads))

    assert read_frames(bytes(transport.writer.data), decrypt) == payloads


@pytest.mark.asyncio
async def test_cancelled_obfuscated_send_still_writes_its_payload(four_crypto_threads, monkeypatch):
    started = threading.Event()
    real_encrypt = aes.ctr256_encrypt

    def encrypt(*args):
        started.set()
        time.sleep(0.1)
        return real_encrypt(*args)

    monkeypatch.setattr(tcp_abridged_o.aes, "ctr256_encrypt", encrypt)
    transport, decrypt = obfuscated_transport()
    first, second = os.urandom(400), os.urandom(800)

    task = asyncio.create_task(transport.send(first))
    await asyncio.get_running_loop().run_in_executor(None, started.wait, 5)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    await transport.send(second)

    # The first payload had moved the CTR state on: had it not been written, the second would decrypt as garbage
    assert read_frames(bytes(transport.writer.data), decrypt) == [first, second]
