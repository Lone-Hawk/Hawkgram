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
from typing import Optional, Dict

import pyrogram
from pyrogram import raw, enums, utils
from pyrogram import types
from ..object import Object

# Display flags of a formatted date, kept so the entity can be written back unchanged
_DATE_FLAGS = ("relative", "short_time", "long_time", "short_date", "long_date", "day_of_week")


class MessageEntity(Object):
    """One special entity in a text message.
    
    For example, hashtags, usernames, URLs, etc.

    Parameters:
        type (:obj:`~pyrogram.enums.MessageEntityType`):
            Type of the entity.

        offset (``int``):
            Offset in UTF-16 code units to the start of the entity.

        length (``int``):
            Length of the entity in UTF-16 code units.

        url (``str``, *optional*):
            For :obj:`~pyrogram.enums.MessageEntityType.TEXT_LINK` only, url that will be opened after user taps on the text.

        user (:obj:`~pyrogram.types.User`, *optional*):
            For :obj:`~pyrogram.enums.MessageEntityType.TEXT_MENTION` only, the mentioned user.

        language (``str``, *optional*):
            For "pre" only, the programming language of the entity text.

        custom_emoji_id (``int``, *optional*):
            For :obj:`~pyrogram.enums.MessageEntityType.CUSTOM_EMOJI` only, unique identifier of the custom emoji.
            Use :meth:`~pyrogram.Client.get_custom_emoji_stickers` to get full information about the sticker.

        collapsed (``bool``, *optional*):
            For :obj:`~pyrogram.enums.MessageEntityType.BLOCKQUOTE` only, whether the blockquote expandable.

        old_text (``str``, *optional*):
            For :obj:`~pyrogram.enums.MessageEntityType.DIFF_REPLACE` only, the text that was replaced.

        date (:py:obj:`~datetime.datetime`, *optional*):
            For :obj:`~pyrogram.enums.MessageEntityType.FORMATTED_DATE` only, the point in time that is shown.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        type: "enums.MessageEntityType",
        offset: int,
        length: int,
        url: str = None,
        user: "types.User" = None,
        language: str = None,
        custom_emoji_id: int = None,
        collapsed: bool = None,
        old_text: str = None,
        date: datetime = None
    ):
        super().__init__(client)

        self.type = type
        self.offset = offset
        self.length = length
        self.url = url
        self.user = user
        self.language = language
        self.custom_emoji_id = custom_emoji_id
        self.collapsed = collapsed
        self.old_text = old_text
        self.date = date
        self._date_flags = {}

    @staticmethod
    def _parse(
        client,
        entity: "raw.base.MessageEntity",
        users: Dict[int, "raw.types.User"] = None
    ) -> Optional["MessageEntity"]:
        # Special case for InputMessageEntityMentionName -> MessageEntityType.TEXT_MENTION
        # This happens in case of UpdateShortSentMessage inside send_message() where entities are parsed from the input
        if isinstance(entity, raw.types.InputMessageEntityMentionName):
            entity_type = enums.MessageEntityType.TEXT_MENTION
            user_id = entity.user_id.user_id
        else:
            # An entity type added by a newer layer must not make the whole message unparsable
            try:
                entity_type = enums.MessageEntityType(entity.__class__)
            except ValueError:
                entity_type = enums.MessageEntityType.UNKNOWN
            user_id = getattr(entity, "user_id", None)

        parsed = MessageEntity(
            type=entity_type,
            offset=entity.offset,
            length=entity.length,
            url=getattr(entity, "url", None),
            user=types.User._parse(client, users.get(user_id, None)),
            language=getattr(entity, "language", None),
            custom_emoji_id=getattr(entity, "document_id", None),
            collapsed=getattr(entity, "collapsed", None),
            old_text=getattr(entity, "old_text", None),
            date=utils.timestamp_to_datetime(getattr(entity, "date", None)),
            client=client
        )

        if entity_type == enums.MessageEntityType.FORMATTED_DATE:
            parsed._date_flags = {flag: getattr(entity, flag) for flag in _DATE_FLAGS if getattr(entity, flag)}

        return parsed

    async def write(self):
        # An unknown entity may still carry fields of the type it came from, which MessageEntityUnknown can't take
        if self.type == enums.MessageEntityType.UNKNOWN:
            return raw.types.MessageEntityUnknown(offset=self.offset, length=self.length)

        args = self.__dict__.copy()

        for arg in ("_client", "type", "user", "_date_flags"):
            args.pop(arg)

        if self.user:
            args["user_id"] = await self._client.resolve_peer(self.user.id)

        if not self.url:
            args.pop("url")

        if self.language is None:
            args.pop("language")

        args.pop("custom_emoji_id")
        if self.custom_emoji_id is not None:
            args["document_id"] = self.custom_emoji_id

        if self.type not in [
            enums.MessageEntityType.BLOCKQUOTE,
            enums.MessageEntityType.EXPANDABLE_BLOCKQUOTE
        ]:
            args.pop("collapsed")

        if self.type != enums.MessageEntityType.DIFF_REPLACE:
            args.pop("old_text")

        args.pop("date")
        if self.type == enums.MessageEntityType.FORMATTED_DATE:
            args["date"] = utils.datetime_to_timestamp(self.date)
            args.update(self._date_flags)

        entity = self.type.value

        if entity is raw.types.MessageEntityMentionName:
            entity = raw.types.InputMessageEntityMentionName

        return entity(**args)
