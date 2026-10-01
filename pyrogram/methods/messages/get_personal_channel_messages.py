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

from typing import List, Union

import pyrogram
from pyrogram import raw, types, utils


class GetPersonalChannelMessages:
    async def get_personal_channel_messages(
        self: "pyrogram.Client",
        user_id: Union[int, str],
        limit: int = 100
    ) -> List["types.Message"]:
        """Get the latest messages of the personal channel shown on the profile of a user.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the user.

            limit (``int``, *optional*):
                Maximum number of messages to return, up to 100. Defaults to 100.

        Returns:
            List of :obj:`~pyrogram.types.Message`: On success, the messages are returned.

        Example:
            .. code-block:: python

                for message in await app.get_personal_channel_messages("username", limit=5):
                    print(message.text)
        """
        r = await self.invoke(
            raw.functions.messages.GetPersonalChannelHistory(
                user_id=utils.get_input_user(await self.resolve_peer(user_id)),
                limit=min(100, limit),
                max_id=0,
                min_id=0,
                hash=0
            )
        )

        if isinstance(r, raw.types.messages.MessagesNotModified):
            return types.List()

        users = {u.id: u for u in r.users}
        chats = {c.id: c for c in r.chats}

        return types.List([
            await types.Message._parse(self, message, users, chats, replies=0)
            for message in r.messages
            if not isinstance(message, raw.types.MessageEmpty)
        ])
