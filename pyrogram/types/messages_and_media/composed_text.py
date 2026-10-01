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

from typing import List, Optional

import pyrogram
from pyrogram import raw, types

from ..object import Object


class ComposedText(Object):
    """A text rewritten, proofread, translated or emojified with AI.

    Parameters:
        text (``str``):
            The resulting text.

        entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
            Special entities of the resulting text.

        diff_text (``str``, *optional*):
            The resulting text with the changes marked by entities of the types
            :obj:`~pyrogram.enums.MessageEntityType.DIFF_INSERT`, :obj:`~pyrogram.enums.MessageEntityType.DIFF_DELETE`
            and :obj:`~pyrogram.enums.MessageEntityType.DIFF_REPLACE`. Returned when proofreading.

        diff_entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
            Special entities of *diff_text*.
    """

    def __init__(
        self,
        *,
        text: str,
        entities: Optional[List["types.MessageEntity"]] = None,
        diff_text: Optional[str] = None,
        diff_entities: Optional[List["types.MessageEntity"]] = None
    ):
        super().__init__()

        self.text = text
        self.entities = entities
        self.diff_text = diff_text
        self.diff_entities = diff_entities

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        composed: "raw.types.messages.ComposedMessageWithAI"
    ) -> "ComposedText":
        text, entities = types.AiComposeToneExample._parse_text(client, composed.result_text)
        diff_text, diff_entities = None, None

        if composed.diff_text is not None:
            diff_text, diff_entities = types.AiComposeToneExample._parse_text(client, composed.diff_text)

        return ComposedText(
            text=text,
            entities=entities,
            diff_text=diff_text,
            diff_entities=diff_entities
        )
