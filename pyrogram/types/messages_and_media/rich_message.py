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

from typing import List, Optional

import pyrogram
from pyrogram import raw, types
from pyrogram.raw.core import TLObject

from ..object import Object

# Page block fields that never contain text meant to be read
_SKIPPED_FIELDS = {"url", "webpage_id", "language", "name", "photo_id", "video_id", "document_id", "audio_id"}


def _rich_text_to_str(text) -> str:
    """Flatten a raw RichText tree into plain text."""
    if text is None or isinstance(text, (raw.types.TextEmpty, raw.types.TextImage)):
        return ""

    if isinstance(text, raw.types.TextPlain):
        return text.text

    if isinstance(text, raw.types.TextConcat):
        return "".join(_rich_text_to_str(t) for t in text.texts)

    if isinstance(text, raw.types.TextCustomEmoji):
        return text.alt

    if isinstance(text, raw.types.TextMath):
        return text.source

    # Every other RichText (bold, italic, url, mention, date, diff, ...) wraps its content in "text"
    return _rich_text_to_str(getattr(text, "text", None))


def _is_rich_text(value) -> bool:
    return isinstance(value, TLObject) and type(value).__name__.startswith("Text")


def _block_to_lines(block) -> List[str]:
    """Collect the readable lines of a raw page block, recursing into nested blocks, list items and tables."""
    if _is_rich_text(block):
        line = _rich_text_to_str(block)
        return [line] if line else []

    if isinstance(block, (raw.types.PageBlockMath, raw.types.TextMath)):
        return [block.source]

    lines = []

    for name in getattr(block, "__slots__", []):
        if name in _SKIPPED_FIELDS:
            continue

        value = getattr(block, name, None)

        if isinstance(value, list):
            for item in value:
                if isinstance(item, TLObject):
                    lines.extend(_block_to_lines(item))
        elif isinstance(value, TLObject):
            lines.extend(_block_to_lines(value))

    return lines


class RichMessage(Object):
    """A message with rich formatting: headings, lists, tables, quotes, formulas, media and more.

    Parameters:
        blocks (List of :obj:`~pyrogram.raw.base.PageBlock`):
            Content of the message as raw page blocks.

        photos (List of :obj:`~pyrogram.types.Photo`, *optional*):
            Photos used in the message.

        documents (List of :obj:`~pyrogram.types.Document`, *optional*):
            Documents (videos, animations, audios and other files) used in the message.

        is_rtl (``bool``, *optional*):
            True, if the message must be shown from right to left.

        is_partial (``bool``, *optional*):
            True, if only a part of the message is included.
            Use :meth:`~pyrogram.Client.get_rich_message` to get the full message.

        text (``str``, *property*):
            The whole message as plain text, one block per line.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        blocks: List["raw.base.PageBlock"],
        photos: Optional[List["types.Photo"]] = None,
        documents: Optional[List["types.Document"]] = None,
        is_rtl: Optional[bool] = None,
        is_partial: Optional[bool] = None,
        raw_rich_message: Optional["raw.types.RichMessage"] = None
    ):
        super().__init__(client)

        self.blocks = blocks
        self.photos = photos
        self.documents = documents
        self.is_rtl = is_rtl
        self.is_partial = is_partial
        self._raw = raw_rich_message

    @property
    def text(self) -> str:
        lines = []

        for block in self.blocks:
            lines.extend(_block_to_lines(block))

        return "\n".join(line for line in lines if line)

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        rich_message: "raw.types.RichMessage"
    ) -> Optional["RichMessage"]:
        if rich_message is None:
            return None

        photos = [types.Photo._parse(client, p) for p in rich_message.photos or []]
        documents = []

        for document in rich_message.documents or []:
            if not isinstance(document, raw.types.Document):
                continue

            attributes = {type(a): a for a in document.attributes}
            file_name = getattr(attributes.get(raw.types.DocumentAttributeFilename), "file_name", None)
            documents.append(types.Document._parse(client, document, file_name))

        return RichMessage(
            client=client,
            blocks=types.List(rich_message.blocks),
            photos=types.List(filter(None, photos)) or None,
            documents=types.List(documents) or None,
            is_rtl=rich_message.rtl,
            is_partial=rich_message.part,
            raw_rich_message=rich_message
        )

    def write(self) -> "raw.types.InputRichMessage":
        """Convert this rich message back into a sendable input, e.g. to send a translated or AI-composed message."""
        source = self._raw

        photos = [
            raw.types.InputPhoto(id=p.id, access_hash=p.access_hash, file_reference=p.file_reference)
            for p in (source.photos if source else [])
            if isinstance(p, raw.types.Photo)
        ]
        documents = [
            raw.types.InputDocument(id=d.id, access_hash=d.access_hash, file_reference=d.file_reference)
            for d in (source.documents if source else [])
            if isinstance(d, raw.types.Document)
        ]

        return raw.types.InputRichMessage(
            blocks=list(self.blocks),
            rtl=self.is_rtl or None,
            photos=photos or None,
            documents=documents or None
        )

    @staticmethod
    def _build_input(
        html: Optional[str] = None,
        markdown: Optional[str] = None,
        rich_message: Optional["RichMessage"] = None,
        is_rtl: Optional[bool] = None,
        disable_auto_links: Optional[bool] = None
    ) -> "raw.base.InputRichMessage":
        """Build a raw input rich message from exactly one of *html*, *markdown* or *rich_message*."""
        if sum(x is not None for x in (html, markdown, rich_message)) != 1:
            raise ValueError("Pass exactly one of html, markdown or rich_message")

        if rich_message is not None:
            input_rich_message = rich_message.write()

            if is_rtl is not None:
                input_rich_message.rtl = is_rtl or None

            if disable_auto_links is not None:
                input_rich_message.noautolink = disable_auto_links or None

            return input_rich_message

        if html is not None:
            return raw.types.InputRichMessageHTML(
                html=html,
                rtl=is_rtl or None,
                noautolink=disable_auto_links or None
            )

        return raw.types.InputRichMessageMarkdown(
            markdown=markdown,
            rtl=is_rtl or None,
            noautolink=disable_auto_links or None
        )
