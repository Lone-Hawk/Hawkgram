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

from typing import List, Optional, Union

import pyrogram
from pyrogram import raw, types


class GetUnreadPollVotes:
    async def get_unread_poll_votes(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        limit: int = 100,
        message_thread_id: Optional[int] = None
    ) -> List["types.Message"]:
        """Get the poll messages of a chat that have votes the current user hasn't seen yet.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            limit (``int``, *optional*):
                Maximum number of messages to return, up to 100. Defaults to 100.

            message_thread_id (``int``, *optional*):
                Unique identifier of a forum topic, to get only the polls of that topic.

        Returns:
            List of :obj:`~pyrogram.types.Message`: On success, the poll messages are returned.

        Example:
            .. code-block:: python

                for message in await app.get_unread_poll_votes(chat_id):
                    print(message.poll.question)
        """
        r = await self.invoke(
            raw.functions.messages.GetUnreadPollVotes(
                peer=await self.resolve_peer(chat_id),
                top_msg_id=message_thread_id,
                offset_id=0,
                add_offset=0,
                limit=min(100, limit),
                max_id=0,
                min_id=0
            )
        )

        users = {u.id: u for u in r.users}
        chats = {c.id: c for c in r.chats}

        return types.List([
            await types.Message._parse(self, message, users, chats, replies=0)
            for message in r.messages
            if not isinstance(message, raw.types.MessageEmpty)
        ])
