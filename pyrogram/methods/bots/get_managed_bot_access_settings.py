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

from typing import Union

import pyrogram
from pyrogram import raw, types, utils


class GetManagedBotAccessSettings:
    async def get_managed_bot_access_settings(
        self: "pyrogram.Client",
        bot_id: Union[int, str]
    ) -> "types.BotAccessSettings":
        """Get which users can use a bot managed by the current bot.

        .. include:: /_includes/usable-by/bots.rst

        Parameters:
            bot_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the managed bot.

        Returns:
            :obj:`~pyrogram.types.BotAccessSettings`: On success, the access settings are returned.

        Example:
            .. code-block:: python

                settings = await app.get_managed_bot_access_settings(bot_id)
        """
        r = await self.invoke(
            raw.functions.bots.GetAccessSettings(
                bot=utils.get_input_user(await self.resolve_peer(bot_id))
            )
        )

        return types.BotAccessSettings._parse(self, r)
