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

from typing import AsyncGenerator, Optional, Union

import pyrogram
from pyrogram import raw, types, utils


class GetCommunityLinkRequests:
    async def get_community_link_requests(
        self: "pyrogram.Client",
        community_id: Union[int, str],
        limit: int = 0
    ) -> Optional[AsyncGenerator["types.CommunityLinkRequest", None]]:
        """Get the pending requests to add chats to a community.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            community_id (``int`` | ``str``):
                Unique identifier of the community.

            limit (``int``, *optional*):
                Limits the number of requests to be retrieved.
                By default, no limit is applied and all requests are returned.

        Returns:
            ``Generator``: A generator yielding :obj:`~pyrogram.types.CommunityLinkRequest` objects.

        Example:
            .. code-block:: python

                async for request in app.get_community_link_requests(community_id):
                    await request.approve()
        """
        community = utils.get_input_channel(await self.resolve_peer(community_id))
        parsed_community_id = utils.get_channel_id(community.channel_id)

        current = 0
        total = abs(limit) or (1 << 31) - 1
        offset = ""

        while True:
            r = await self.invoke(
                raw.functions.communities.GetPeerLinkRequests(
                    community=community,
                    offset=offset,
                    limit=min(100, total - current)
                )
            )

            users = {i.id: i for i in r.users}
            chats = {i.id: i for i in r.chats}

            for request in r.requests:
                yield types.CommunityLinkRequest._parse(self, parsed_community_id, request, users, chats)

                current += 1

                if current >= total:
                    return

            if not r.next_offset or not r.requests:
                return

            offset = r.next_offset
