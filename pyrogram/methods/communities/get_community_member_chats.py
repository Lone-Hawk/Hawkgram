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

from typing import Union

import pyrogram
from pyrogram import raw, types, utils


class GetCommunityMemberChats:
    async def get_community_member_chats(
        self: "pyrogram.Client",
        community_id: Union[int, str],
        user_id: Union[int, str]
    ) -> "types.CommunityMemberChats":
        """Get the chats of a community that a member created or joined.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            community_id (``int`` | ``str``):
                Unique identifier of the community.

            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the member.

        Returns:
            :obj:`~pyrogram.types.CommunityMemberChats`: On success, the chats of the member are returned.

        Example:
            .. code-block:: python

                chats = await app.get_community_member_chats(community_id, "username")
                print(chats.joined_chats)
        """
        r = await self.invoke(
            raw.functions.communities.GetParticipantJoinedChats(
                community=utils.get_input_channel(await self.resolve_peer(community_id)),
                participant=await self.resolve_peer(user_id)
            )
        )

        return types.CommunityMemberChats._parse(self, r)
