#  Hawkgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2026-present Lone Hawk
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

from enum import auto

from .auto_name import AutoName


class ChatJoinQueryResult(AutoName):
    """Result of a join query handled by a guard bot, used in :meth:`~pyrogram.Client.answer_chat_join_query`."""

    APPROVED = auto()
    "The user is allowed to join the chat"

    DECLINED = auto()
    "The user isn't allowed to join the chat"

    QUEUED = auto()
    "The join request is added to the list of pending join requests for chat administrators to review"
