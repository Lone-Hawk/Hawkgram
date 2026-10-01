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

from typing import Dict, Optional, Union

import pyrogram
from pyrogram import raw, types

from ..object import Object


class AiComposeTone(Object):
    """A tone (writing style) used to rewrite, translate or compose texts with AI.

    Tones are either built-in tones provided by Telegram, or custom tones created by users with a prompt.

    Parameters:
        name (``str``):
            Name of the tone. For built-in tones this is the tone identifier, for custom tones this is the
            unique slug that can be shared with other users.

        title (``str``):
            Title of the tone.

        is_default (``bool``):
            True, if the tone is one of the built-in tones provided by Telegram.

        id (``int``, *optional*):
            Unique identifier of a custom tone.

        custom_emoji_id (``int``, *optional*):
            Identifier of the custom emoji shown for the tone.

        prompt (``str``, *optional*):
            Prompt used by a custom tone. Available only for tones created by the current user.

        install_count (``int``, *optional*):
            Number of users that added the custom tone.

        author (:obj:`~pyrogram.types.User`, *optional*):
            Creator of the tone, if the creator chose to be shown.

        is_creator (``bool``, *optional*):
            True, if the tone was created by the current user.

        example (:obj:`~pyrogram.types.AiComposeToneExample`, *optional*):
            An example of the tone applied to an English text.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        name: str,
        title: str,
        is_default: bool,
        id: Optional[int] = None,
        custom_emoji_id: Optional[int] = None,
        prompt: Optional[str] = None,
        install_count: Optional[int] = None,
        author: Optional["types.User"] = None,
        is_creator: Optional[bool] = None,
        example: Optional["types.AiComposeToneExample"] = None,
        access_hash: Optional[int] = None
    ):
        super().__init__(client)

        self.name = name
        self.title = title
        self.is_default = is_default
        self.id = id
        self.custom_emoji_id = custom_emoji_id
        self.prompt = prompt
        self.install_count = install_count
        self.author = author
        self.is_creator = is_creator
        self.example = example
        self._access_hash = access_hash

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        tone: "raw.base.AiComposeTone",
        users: Dict[int, "raw.types.User"] = None
    ) -> Optional["AiComposeTone"]:
        users = users or {}

        if isinstance(tone, raw.types.AiComposeToneDefault):
            return AiComposeTone(
                client=client,
                name=tone.tone,
                title=tone.title,
                is_default=True,
                custom_emoji_id=tone.emoji_id
            )

        if isinstance(tone, raw.types.AiComposeTone):
            author_id = getattr(tone, "author_id", None)

            return AiComposeTone(
                client=client,
                name=tone.slug,
                title=tone.title,
                is_default=False,
                id=tone.id,
                custom_emoji_id=tone.emoji_id,
                prompt=tone.prompt,
                install_count=tone.installs_count,
                author=types.User._parse(client, users.get(author_id)) if author_id else None,
                is_creator=tone.creator,
                example=types.AiComposeToneExample._parse(client, tone.example_english),
                access_hash=tone.access_hash
            )

        return None

    def write(self) -> "raw.base.InputAiComposeTone":
        if self.is_default:
            return raw.types.InputAiComposeToneDefault(tone=self.name)

        if self.id is not None and self._access_hash is not None:
            return raw.types.InputAiComposeToneID(id=self.id, access_hash=self._access_hash)

        return raw.types.InputAiComposeToneSlug(slug=self.name)

    @staticmethod
    def _to_input(
        tone: Union["AiComposeTone", str, "raw.base.InputAiComposeTone", None]
    ) -> Optional["raw.base.InputAiComposeTone"]:
        """Convert the *tone* argument accepted by methods into a raw input tone.

        A string is treated as the slug of a custom tone.
        """
        if tone is None:
            return None

        if isinstance(tone, AiComposeTone):
            return tone.write()

        if isinstance(tone, str):
            return raw.types.InputAiComposeToneSlug(slug=tone)

        if isinstance(tone, (
            raw.types.InputAiComposeToneDefault,
            raw.types.InputAiComposeToneID,
            raw.types.InputAiComposeToneSlug,
            raw.types.InputAiComposeToneSingleUse
        )):
            return tone

        raise TypeError(f"tone must be an AiComposeTone or a tone slug (str), not {type(tone).__name__}")
