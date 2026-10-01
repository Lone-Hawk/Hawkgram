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
from ..update import Update


class ManagedBotUpdated(Object, Update):
    """A bot managed by the current bot was created or changed.

    Parameters:
        bot_id (``int``):
            User identifier of the managed bot.

        user (:obj:`~pyrogram.types.User`, *optional*):
            The user who created the managed bot.

        bot (:obj:`~pyrogram.types.User`, *optional*):
            The managed bot, if known.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        bot_id: int,
        user: Optional["types.User"] = None,
        bot: Optional["types.User"] = None
    ):
        super().__init__(client)

        self.bot_id = bot_id
        self.user = user
        self.bot = bot

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        update: "raw.types.UpdateManagedBot",
        users: Dict[int, "raw.types.User"]
    ) -> "ManagedBotUpdated":
        return ManagedBotUpdated(
            client=client,
            bot_id=update.bot_id,
            user=types.User._parse(client, users.get(update.user_id)),
            bot=types.User._parse(client, users.get(update.bot_id))
        )
