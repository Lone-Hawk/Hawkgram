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
from pyrogram import raw, utils


class GetManagedBotToken:
    async def get_managed_bot_token(
        self: "pyrogram.Client",
        bot_id: Union[int, str],
        revoke: bool = False
    ) -> str:
        """Get the token of a bot managed by the current bot.

        .. include:: /_includes/usable-by/bots.rst

        Parameters:
            bot_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the managed bot.

            revoke (``bool``, *optional*):
                Pass True to revoke the current token and generate a new one.

        Returns:
            ``str``: On success, the bot token is returned.

        Example:
            .. code-block:: python

                token = await app.get_managed_bot_token(bot_id)
        """
        r = await self.invoke(
            raw.functions.bots.ExportBotToken(
                bot=utils.get_input_user(await self.resolve_peer(bot_id)),
                revoke=revoke
            )
        )

        return r.token
