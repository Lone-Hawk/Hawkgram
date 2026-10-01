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

from typing import List, Optional, Union

import pyrogram
from pyrogram import enums, raw, types, utils


class ComposeTextWithAi:
    async def compose_text_with_ai(
        self: "pyrogram.Client",
        text: str,
        parse_mode: Optional["enums.ParseMode"] = None,
        entities: List["types.MessageEntity"] = None,
        tone: Union["types.AiComposeTone", str] = None,
        custom_prompt: Optional[str] = None,
        translate_to_language_code: Optional[str] = None,
        proofread: bool = False,
        add_emojis: bool = False
    ) -> "types.ComposedText":
        """Rewrite, proofread, translate or emojify a text with AI.

        May fail with *AICOMPOSE_FLOOD_PREMIUM* if Telegram Premium is required for further requests.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            text (``str``):
                The original text.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
                List of special entities that appear in the text, which can be specified instead of *parse_mode*.

            tone (:obj:`~pyrogram.types.AiComposeTone` | ``str``, *optional*):
                Tone to rewrite the text with, or the slug of a custom tone.
                See :meth:`~pyrogram.Client.get_ai_compose_tones`.

            custom_prompt (``str``, *optional*):
                A one-time prompt describing how to rewrite the text, used instead of *tone*.

            translate_to_language_code (``str``, *optional*):
                Language code to translate the text to.

            proofread (``bool``, *optional*):
                Pass True to fix spelling and grammar. The result then contains a *diff_text* marking the changes.

            add_emojis (``bool``, *optional*):
                Pass True to add emoji to the text.

        Returns:
            :obj:`~pyrogram.types.ComposedText`: On success, the resulting text is returned.

        Example:
            .. code-block:: python

                # Proofread
                result = await app.compose_text_with_ai("I has a apple", proofread=True)

                # Rewrite with a tone
                tones = await app.get_ai_compose_tones()
                result = await app.compose_text_with_ai("Meeting moved to 5pm", tone=tones[0])
        """
        if tone is not None and custom_prompt is not None:
            raise ValueError("Pass either tone or custom_prompt, not both")

        message, entities = (await utils.parse_text_entities(self, text, parse_mode, entities)).values()

        input_tone = (
            raw.types.InputAiComposeToneSingleUse(custom_prompt=custom_prompt)
            if custom_prompt is not None
            else types.AiComposeTone._to_input(tone)
        )

        r = await self.invoke(
            raw.functions.messages.ComposeMessageWithAI(
                text=raw.types.TextWithEntities(text=message, entities=entities or []),
                tone=input_tone,
                translate_to_lang=translate_to_language_code,
                proofread=proofread or None,
                emojify=add_emojis or None
            )
        )

        return types.ComposedText._parse(self, r)
