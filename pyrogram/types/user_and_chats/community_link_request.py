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

from datetime import datetime
from typing import Dict, Optional

import pyrogram
from pyrogram import raw, types, utils

from ..object import Object


class CommunityLinkRequest(Object):
    """A pending request to add a chat to a community.

    Parameters:
        community_id (``int``):
            Identifier of the community.

        chat (:obj:`~pyrogram.types.Chat`):
            The chat that asks to be added to the community.

        requested_by (:obj:`~pyrogram.types.User`, *optional*):
            The user who sent the request.

        date (:py:obj:`~datetime.datetime`):
            Date the request was sent.

        is_visible (``bool``, *optional*):
            True, if the chat will be visible to all community members once the request is approved.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        community_id: int,
        chat: "types.Chat",
        date: datetime,
        requested_by: Optional["types.User"] = None,
        is_visible: Optional[bool] = None
    ):
        super().__init__(client)

        self.community_id = community_id
        self.chat = chat
        self.date = date
        self.requested_by = requested_by
        self.is_visible = is_visible

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        community_id: int,
        request: "raw.types.CommunityPeerRequest",
        users: Dict[int, "raw.types.User"],
        chats: Dict[int, "raw.types.Chat"]
    ) -> "CommunityLinkRequest":
        return CommunityLinkRequest(
            client=client,
            community_id=community_id,
            chat=types.Chat._parse_dialog(client, request.peer, users, chats),
            date=utils.timestamp_to_datetime(request.date),
            requested_by=types.User._parse(client, users.get(request.requested_by)),
            is_visible=request.visible,
        )

    async def approve(self) -> bool:
        """Bound method *approve* of :obj:`~pyrogram.types.CommunityLinkRequest`.

        Use as a shortcut for :meth:`~pyrogram.Client.approve_community_link_request`.

        Example:
            .. code-block:: python

                await request.approve()
        """
        return await self._client.approve_community_link_request(self.community_id, self.chat.id)

    async def decline(self) -> bool:
        """Bound method *decline* of :obj:`~pyrogram.types.CommunityLinkRequest`.

        Use as a shortcut for :meth:`~pyrogram.Client.decline_community_link_request`.

        Example:
            .. code-block:: python

                await request.decline()
        """
        return await self._client.decline_community_link_request(self.community_id, self.chat.id)
