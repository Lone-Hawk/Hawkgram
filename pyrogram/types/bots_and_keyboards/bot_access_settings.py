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

from typing import List, Optional

import pyrogram
from pyrogram import raw, types

from ..object import Object


class BotAccessSettings(Object):
    """Describes which users can use a managed bot.

    Parameters:
        is_restricted (``bool``):
            True, if only the owner of the bot and the users in *allowed_users* can use the bot.

        allowed_users (List of :obj:`~pyrogram.types.User`, *optional*):
            Users that can use the bot in addition to its owner.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        is_restricted: bool,
        allowed_users: Optional[List["types.User"]] = None
    ):
        super().__init__(client)

        self.is_restricted = is_restricted
        self.allowed_users = allowed_users

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        settings: "raw.types.bots.AccessSettings"
    ) -> "BotAccessSettings":
        allowed_users = types.List(filter(None, [
            types.User._parse(client, user) for user in settings.add_users or []
        ]))

        return BotAccessSettings(
            client=client,
            is_restricted=bool(settings.restricted),
            allowed_users=allowed_users or None
        )
