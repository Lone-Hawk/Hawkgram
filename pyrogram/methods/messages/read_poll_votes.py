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

from typing import Optional, Union

import pyrogram
from pyrogram import raw


class ReadPollVotes:
    async def read_poll_votes(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        message_thread_id: Optional[int] = None
    ) -> bool:
        """Mark all poll votes of a chat as read.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            message_thread_id (``int``, *optional*):
                Unique identifier of a forum topic, to mark as read only the poll votes of that topic.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.read_poll_votes(chat_id)
        """
        await self.invoke(
            raw.functions.messages.ReadPollVotes(
                peer=await self.resolve_peer(chat_id),
                top_msg_id=message_thread_id
            )
        )

        return True
