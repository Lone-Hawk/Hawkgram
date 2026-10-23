#  Hawkgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#  Copyright (C) 2022-present Mayuri-Chan <https://github.com/Mayuri-Chan>
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

import asyncio
from typing import Optional


class Turn:
    """A place in a :class:`Sequencer`'s order"""

    __slots__ = ("previous", "finished")

    def __init__(self, previous: Optional[asyncio.Future]):
        self.previous = previous
        self.finished = asyncio.get_running_loop().create_future()

    async def wait(self) -> None:
        """Wait until every earlier turn is done"""
        if self.previous is not None and not self.previous.done():
            # Shielded: a cancelled waiter must not cancel the turn before it, which would let the next one go early
            await asyncio.shield(self.previous)

    def done(self) -> None:
        """End this turn, also when it was cancelled or failed. The next turn starts once the earlier ones are done."""
        if self.finished.done():
            return

        if self.previous is None or self.previous.done():
            self.finished.set_result(None)
        else:
            self.previous.add_done_callback(lambda _: self.done())


class Sequencer:
    """Let concurrent tasks do the slow part of their work at once and the rest one by one, in the order they came.

    A session encrypts the messages it sends and decrypts the packets it receives in the crypto thread pool. With its
    one thread the results come back in the order the calls were made, but nothing else guaranteed that: with more
    threads (pyrogram.crypto_executor can be replaced) they come back in any order. The order matters: Telegram
    rejects messages sent with a msg_id or seq_no lower than one it has already received, and received messages are
    checked against the msg_ids before them and passed on as updates in order. So each task takes a turn before its
    slow part, and waits for it before the part that must happen in order::

        turn = sequencer.take()

        try:
            payload = await encrypt(message)  # concurrent
            await turn.wait()
            await connection.send(payload)  # in order
        finally:
            turn.done()
    """

    def __init__(self):
        self.last: Optional[asyncio.Future] = None

    def take(self) -> Turn:
        """Take the next turn. Call it in the order the work must be done, before the first await."""
        turn = Turn(self.last)
        self.last = turn.finished

        return turn
