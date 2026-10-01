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
from pyrogram import raw, types


class GetRichMessage:
    async def get_rich_message(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        message_id: int
    ) -> Optional["types.Message"]:
        """Get the full version of a rich message.

        Messages received in updates or history may contain only a part of a long rich message
        (see :obj:`~pyrogram.types.RichMessage.is_partial`).

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            message_id (``int``):
                Identifier of the message.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the message with the full rich message is returned.

        Example:
            .. code-block:: python

                message = await app.get_rich_message(chat_id, message_id)
                print(message.rich_message.text)
        """
        r = await self.invoke(
            raw.functions.messages.GetRichMessage(
                peer=await self.resolve_peer(chat_id),
                id=message_id
            )
        )

        users = {u.id: u for u in r.users}
        chats = {c.id: c for c in r.chats}

        for message in r.messages:
            if not isinstance(message, raw.types.MessageEmpty):
                return await types.Message._parse(self, message, users, chats, replies=0)

        return None
