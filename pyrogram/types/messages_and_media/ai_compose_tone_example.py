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

from typing import List, Optional, Tuple

import pyrogram
from pyrogram import raw, types

from ..object import Object
from .message import Str


class AiComposeToneExample(Object):
    """An example of a text before and after applying an AI compose tone.

    Parameters:
        text (``str``):
            The original text.

        result_text (``str``):
            The text after the tone was applied.

        entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
            Special entities of the original text.

        result_entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
            Special entities of the resulting text.
    """

    def __init__(
        self,
        *,
        text: str,
        result_text: str,
        entities: Optional[List["types.MessageEntity"]] = None,
        result_entities: Optional[List["types.MessageEntity"]] = None
    ):
        super().__init__()

        self.text = text
        self.result_text = result_text
        self.entities = entities
        self.result_entities = result_entities

    @staticmethod
    def _parse_text(
        client: "pyrogram.Client",
        text_with_entities: "raw.types.TextWithEntities"
    ) -> Tuple[str, Optional[List["types.MessageEntity"]]]:
        entities = types.List(filter(None, [
            types.MessageEntity._parse(client, entity, {})
            for entity in text_with_entities.entities or []
        ]))

        return Str(text_with_entities.text).init(entities), entities or None

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        example: "raw.types.AiComposeToneExample"
    ) -> Optional["AiComposeToneExample"]:
        if example is None:
            return None

        # The raw "from" field is renamed to "from_peer" by the API compiler, since "from" is a Python keyword
        text, entities = AiComposeToneExample._parse_text(client, example.from_peer)
        result_text, result_entities = AiComposeToneExample._parse_text(client, example.to)

        return AiComposeToneExample(
            text=text,
            result_text=result_text,
            entities=entities,
            result_entities=result_entities
        )
