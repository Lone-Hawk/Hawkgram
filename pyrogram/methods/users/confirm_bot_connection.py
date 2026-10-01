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


class ConfirmBotConnection:
    async def confirm_bot_connection(
        self: "pyrogram.Client",
        bot_id: Union[int, str]
    ) -> bool:
        """Confirm the connection of a bot to the account of the current user.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            bot_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the bot.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.confirm_bot_connection("my_business_bot")
        """
        return await self.invoke(
            raw.functions.account.ConfirmBotConnection(
                bot_id=utils.get_input_user(await self.resolve_peer(bot_id))
            )
        )
