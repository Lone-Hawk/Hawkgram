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

from ..object import Object


class CommunityMemberChats(Object):
    """Chats of a community that a member created or joined.

    Parameters:
        created_chats (List of :obj:`~pyrogram.types.Chat`):
            Chats of the community created by the member.

        joined_chats (List of :obj:`~pyrogram.types.Chat`):
            Chats of the community the member joined.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        created_chats: List["types.Chat"],
        joined_chats: List["types.Chat"]
    ):
        super().__init__(client)

        self.created_chats = created_chats
        self.joined_chats = joined_chats

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        result: "raw.types.communities.ParticipantJoinedChats"
    ) -> "CommunityMemberChats":
        chats = {c.id: c for c in result.chats}
        users = {u.id: u for u in result.users}

        def resolve(raw_ids):
            parsed = []

            for raw_id in raw_ids:
                if raw_id in chats:
                    parsed.append(types.Chat._parse_chat(client, chats[raw_id]))
                elif raw_id in users:
                    parsed.append(types.Chat._parse_user_chat(client, users[raw_id]))

            return types.List(filter(None, parsed))

        return CommunityMemberChats(
            client=client,
            created_chats=resolve(result.creator_chat_ids),
            joined_chats=resolve(result.joined_chat_ids)
        )
