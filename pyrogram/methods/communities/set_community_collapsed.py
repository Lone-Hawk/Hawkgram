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


class SetCommunityCollapsed:
    async def set_community_collapsed(
        self: "pyrogram.Client",
        community_id: Union[int, str],
        is_collapsed: bool = True
    ) -> bool:
        """Collapse the chats of a community into a single entry of the chat list, or expand them again.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            community_id (``int`` | ``str``):
                Unique identifier of the community.

            is_collapsed (``bool``, *optional*):
                Pass True to collapse the community, False to expand it. Defaults to True.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                # Collapse
                await app.set_community_collapsed(community_id)

                # Expand
                await app.set_community_collapsed(community_id, False)
        """
        await self.invoke(
            raw.functions.communities.ToggleCommunityCollapsedInDialogs(
                community=utils.get_input_channel(await self.resolve_peer(community_id)),
                collapsed=is_collapsed or None
            )
        )

        return True
