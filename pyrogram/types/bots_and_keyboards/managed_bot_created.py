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

from typing import Dict, Optional

import pyrogram
from pyrogram import raw, types

from ..object import Object


class ManagedBotCreated(Object):
    """A service message about a bot, managed by another bot, that was created by the user.

    Parameters:
        bot_id (``int``):
            User identifier of the created bot.

        bot (:obj:`~pyrogram.types.User`, *optional*):
            The created bot, if known.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        bot_id: int,
        bot: Optional["types.User"] = None
    ):
        super().__init__(client)

        self.bot_id = bot_id
        self.bot = bot

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        action: "raw.types.MessageActionManagedBotCreated",
        users: Dict[int, "raw.types.User"]
    ) -> "ManagedBotCreated":
        return ManagedBotCreated(
            client=client,
            bot_id=action.bot_id,
            bot=types.User._parse(client, (users or {}).get(action.bot_id))
        )
