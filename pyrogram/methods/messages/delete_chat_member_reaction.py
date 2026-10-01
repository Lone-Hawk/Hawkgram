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
from pyrogram import raw


class DeleteChatMemberReaction:
    async def delete_chat_member_reaction(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        message_id: int,
        user_id: Union[int, str]
    ) -> bool:
        """Remove the reaction of a chat member from a message.

        Requires administrator rights in the chat.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            message_id (``int``):
                Identifier of the message.

            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the member whose reaction is removed.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.delete_chat_member_reaction(chat_id, message_id, user_id)
        """
        await self.invoke(
            raw.functions.messages.DeleteParticipantReaction(
                peer=await self.resolve_peer(chat_id),
                msg_id=message_id,
                participant=await self.resolve_peer(user_id)
            )
        )

        return True
