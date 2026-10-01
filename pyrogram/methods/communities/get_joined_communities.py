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

from typing import List

import pyrogram
from pyrogram import raw, types


class GetJoinedCommunities:
    async def get_joined_communities(
        self: "pyrogram.Client"
    ) -> List["types.Chat"]:
        """Get the communities the current user belongs to.

        .. include:: /_includes/usable-by/users.rst

        Returns:
            List of :obj:`~pyrogram.types.Chat`: On success, the list of communities is returned.

        Example:
            .. code-block:: python

                for community in await app.get_joined_communities():
                    print(community.title)
        """
        r = await self.invoke(raw.functions.communities.GetJoinedCommunities())

        return types.List(
            types.Chat._parse_community_chat(self, chat)
            for chat in r.chats
            if isinstance(chat, (raw.types.Community, raw.types.CommunityForbidden))
        )
