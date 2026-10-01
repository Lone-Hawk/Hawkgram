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


class SetCommunityChatHidden:
    async def set_community_chat_hidden(
        self: "pyrogram.Client",
        community_id: Union[int, str],
        chat_id: Union[int, str],
        is_hidden: bool = True
    ) -> bool:
        """Hide a chat of a community from its members, or show it again.

        Hidden chats are visible only to administrators of the community.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            community_id (``int`` | ``str``):
                Unique identifier of the community.

            chat_id (``int`` | ``str``):
                Unique identifier of the chat in the community.

            is_hidden (``bool``, *optional*):
                Pass True to hide the chat, False to show it. Defaults to True.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.set_community_chat_hidden(community_id, chat_id)
        """
        return await self.invoke(
            raw.functions.communities.TogglePeerLink(
                community=utils.get_input_channel(await self.resolve_peer(community_id)),
                peer=await self.resolve_peer(chat_id),
                hidden=is_hidden or None,
                visible=(not is_hidden) or None
            )
        )
