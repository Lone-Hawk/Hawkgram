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

from typing import List, Union

import pyrogram
from pyrogram import raw, types


class GetWelcomeMessages:
    async def get_welcome_messages(
        self: "pyrogram.Client",
        chat_id: Union[int, str]
    ) -> List["types.EphemeralMessage"]:
        """Get the welcome messages of a chat, shown privately to users who join the chat.

        Requires administrator rights to manage welcome messages in the chat.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

        Returns:
            List of :obj:`~pyrogram.types.EphemeralMessage`: On success, the welcome messages are returned.

        Example:
            .. code-block:: python

                for message in await app.get_welcome_messages(chat_id):
                    print(message.text)
        """
        r = await self.invoke(
            raw.functions.ephemeral.GetWelcomeMessages(
                peer=await self.resolve_peer(chat_id),
                hash=0
            )
        )

        if not isinstance(r, raw.types.ephemeral.WelcomeMessages):
            return types.List()

        users, chats = await types.EphemeralMessage._fetch_peers(self, chat_id)

        return types.List([
            await types.EphemeralMessage._parse_ephemeral(self, message, users, chats)
            for message in r.messages
        ])
