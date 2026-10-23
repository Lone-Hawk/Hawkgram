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

"""Regression tests for the dispatcher: errors in handlers are reported"""

import asyncio
import logging

import pytest

from pyrogram import raw
from pyrogram.handlers import RawUpdateHandler
from .test_layer_229 import FakeClient


@pytest.mark.asyncio
async def test_raw_update_handler_errors_are_logged(caplog):
    client = FakeClient()
    calls = []

    async def failing(client, update, users, chats):
        calls.append(update)
        raise RuntimeError("raw handler failed")

    client.dispatcher.groups[1] = [RawUpdateHandler(failing)]
    # An update no parser knows: raw handlers get it, but there is no parsed update for the error handlers
    update = raw.types.UpdateConfig()

    with caplog.at_level(logging.ERROR, logger="pyrogram.dispatcher"):
        await client.dispatcher._handle_packet((update, {}, {}), asyncio.Lock())

    assert calls == [update]
    # The error used to vanish without a trace
    assert "raw handler failed" in caplog.text
