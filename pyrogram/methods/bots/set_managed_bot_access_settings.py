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

from typing import Iterable, Optional, Union

import pyrogram
from pyrogram import raw, utils


class SetManagedBotAccessSettings:
    async def set_managed_bot_access_settings(
        self: "pyrogram.Client",
        bot_id: Union[int, str],
        is_restricted: bool,
        allowed_user_ids: Optional[Iterable[Union[int, str]]] = None
    ) -> bool:
        """Change which users can use a bot managed by the current bot.

        .. include:: /_includes/usable-by/bots.rst

        Parameters:
            bot_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the managed bot.

            is_restricted (``bool``):
                Pass True to allow only the owner of the bot and the users in *allowed_user_ids* to use the bot.

            allowed_user_ids (Iterable of ``int`` | ``str``, *optional*):
                Users that can use the bot in addition to its owner.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.set_managed_bot_access_settings(bot_id, True, [user_id])
        """
        users = [
            utils.get_input_user(await self.resolve_peer(user_id))
            for user_id in allowed_user_ids or []
        ]

        return await self.invoke(
            raw.functions.bots.EditAccessSettings(
                bot=utils.get_input_user(await self.resolve_peer(bot_id)),
                restricted=is_restricted or None,
                add_users=users or None
            )
        )
