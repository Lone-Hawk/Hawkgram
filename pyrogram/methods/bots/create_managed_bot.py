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


class CreateManagedBot:
    async def create_managed_bot(
        self: "pyrogram.Client",
        manager_bot_id: Union[int, str],
        name: str,
        username: str,
        via_link: bool = False
    ) -> "types.User":
        """Create a bot owned by the current user and managed by another bot.

        The manager bot must be able to manage bots. May fail with *BOT_CREATE_LIMIT_EXCEEDED* if the user already
        owns the maximum number of bots.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            manager_bot_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the bot that will manage the new bot.

            name (``str``):
                Name of the new bot, 1-64 characters.

            username (``str``):
                Username of the new bot; must end with "bot". Use :meth:`~pyrogram.Client.check_bot_username`
                to check whether it's available.

            via_link (``bool``, *optional*):
                Pass True if the bot is created from a link requesting the creation of a managed bot.

        Returns:
            :obj:`~pyrogram.types.User`: On success, the created bot is returned.

        Example:
            .. code-block:: python

                bot = await app.create_managed_bot("manager_bot", "My helper", "my_helper_bot")
        """
        r = await self.invoke(
            raw.functions.bots.CreateBot(
                manager_id=utils.get_input_user(await self.resolve_peer(manager_bot_id)),
                name=name,
                username=username,
                via_deeplink=via_link or None
            )
        )

        return types.User._parse(self, r)
