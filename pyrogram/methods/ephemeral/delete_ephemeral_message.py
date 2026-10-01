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


class DeleteEphemeralMessage:
    async def delete_ephemeral_message(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        user_id: Union[int, str],
        message_id: int
    ) -> bool:
        """Delete an ephemeral message sent by the bot.

        .. include:: /_includes/usable-by/bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the user who received the message.

            message_id (``int``):
                Identifier of the ephemeral message.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.delete_ephemeral_message(chat_id, user_id, message_id)
        """
        return await self.invoke(
            raw.functions.ephemeral.DeleteMessage(
                peer=await self.resolve_peer(chat_id),
                receiver_id=utils.get_input_user(await self.resolve_peer(user_id)),
                id=message_id
            )
        )
