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
from pyrogram import raw, utils


class DeclineCommunityLinkRequest:
    async def decline_community_link_request(
        self: "pyrogram.Client",
        community_id: Union[int, str],
        chat_id: Union[int, str]
    ) -> bool:
        """Decline a pending request to add a chat to a community.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            community_id (``int`` | ``str``):
                Unique identifier of the community.

            chat_id (``int`` | ``str``):
                Unique identifier of the chat that asked to be added.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.decline_community_link_request(community_id, chat_id)
        """
        return await self.invoke(
            raw.functions.communities.TogglePeerLinkRequestApproval(
                community=utils.get_input_channel(await self.resolve_peer(community_id)),
                peer=await self.resolve_peer(chat_id),
                reject=True
            )
        )
