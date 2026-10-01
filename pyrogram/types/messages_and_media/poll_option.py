#  Hawkgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#  Copyright (C) 2022-present Mayuri-Chan <https://github.com/Mayuri-Chan>
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
from typing import Dict, List, Optional, Union

import pyrogram
from pyrogram import raw, utils
from ..object import Object


class PollOption(Object):
    """Contains information about one answer option in a poll.

    Parameters:
        text (``str``):
            Option text, 1-100 characters.

        voter_count (``int``, *optional*):
            Number of users that voted for this option.
            Equals to 0 until you vote.

        data (``bytes``, *optional*):
            The data this poll option is holding.

        entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
            Special entities like usernames, URLs, bot commands, etc. that appear in the option text.

        added_by (:obj:`~pyrogram.types.User` | :obj:`~pyrogram.types.Chat`, *optional*):
            The user or chat who added the option after the poll was created.

        added_date (:py:obj:`~datetime.datetime`, *optional*):
            Date the option was added after the poll was created.
    """

    def __init__(
        self: "pyrogram.Client",
        text: str,
        voter_count: int = 0,
        data: bytes = None,
        entities: Optional[List["pyrogram.types.MessageEntity"]] = None,
        added_by: Optional[Union["pyrogram.types.User", "pyrogram.types.Chat"]] = None,
        added_date: Optional[datetime] = None
    ):
        super().__init__(self)

        self.text = text
        self.voter_count = voter_count
        self.data = data
        self.entities = entities
        self.added_by = added_by
        self.added_date = added_date

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        answer: "raw.types.PollAnswer",
        users: Dict[int, "raw.types.User"] = None,
        chats: Dict[int, "raw.types.Chat"] = None
    ) -> "PollOption":
        users = users or {}
        chats = chats or {}

        entities = pyrogram.types.List(filter(None, [
            pyrogram.types.MessageEntity._parse(client, entity, users)
            for entity in answer.text.entities or []
        ]))

        added_by = None
        added_by_peer = getattr(answer, "added_by", None)

        if isinstance(added_by_peer, raw.types.PeerUser):
            added_by = pyrogram.types.User._parse(client, users.get(added_by_peer.user_id))
        elif added_by_peer is not None:
            raw_chat = chats.get(utils.get_raw_peer_id(added_by_peer))
            added_by = pyrogram.types.Chat._parse_chat(client, raw_chat) if raw_chat else None

        return PollOption(
            text=answer.text.text,
            data=getattr(answer, "option", None),
            entities=entities or None,
            added_by=added_by,
            added_date=utils.timestamp_to_datetime(getattr(answer, "date", None))
        )

    async def write(self, client, i):
        option, entities = (await pyrogram.utils.parse_text_entities(client, self.text, None, self.entities)).values()
        return pyrogram.raw.types.PollAnswer(
            text=pyrogram.raw.types.TextWithEntities(
                text=option,
                entities=entities or []
            ),
            option=bytes([i])
        )
