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


class CreateCommunity:
    async def create_community(
        self: "pyrogram.Client",
        title: str,
        chat_id: Union[int, str],
        description: Optional[str] = None,
        is_chat_hidden: bool = False
    ) -> "types.Chat":
        """Create a community, a group of supergroups, channels and chats with bots, starting from one chat.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            title (``str``):
                Name of the new community.

            chat_id (``int`` | ``str``):
                The first chat of the community. Only chats with bots owned by the current user and basic groups,
                supergroups and channels owned by the current user are allowed; basic groups are automatically
                upgraded to supergroups.

            description (``str``, *optional*):
                Description of the community.

            is_chat_hidden (``bool``, *optional*):
                Pass True to show the chat only to administrators of the community.

        Returns:
            :obj:`~pyrogram.types.Chat`: On success, the new community is returned.

        Example:
            .. code-block:: python

                community = await app.create_community("My projects", "my_channel")
        """
        r = await self.invoke(
            raw.functions.communities.Create(
                title=title,
                about=description,
                peer=await self.resolve_peer(chat_id),
                hidden=is_chat_hidden or None
            )
        )

        for chat in r.chats:
            if isinstance(chat, raw.types.Community):
                return types.Chat._parse_community_chat(self, chat)
