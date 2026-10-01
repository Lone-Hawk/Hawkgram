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

from typing import Optional, Union

import pyrogram
from pyrogram import raw, types


class ComposeRichMessageWithAi:
    async def compose_rich_message_with_ai(
        self: "pyrogram.Client",
        html: Optional[str] = None,
        markdown: Optional[str] = None,
        rich_message: Optional["types.RichMessage"] = None,
        tone: Union["types.AiComposeTone", str] = None,
        custom_prompt: Optional[str] = None,
        translate_to_language_code: Optional[str] = None,
        proofread: bool = False,
        add_emojis: bool = False
    ) -> "types.RichMessage":
        """Rewrite, proofread, translate or emojify a rich message with AI, or create a new one from a prompt.

        Pass at most one of *html*, *markdown* or *rich_message*. To create a new message, pass none of them and
        describe the message with *custom_prompt*.

        May fail with *AICOMPOSE_FLOOD_PREMIUM* if Telegram Premium is required for further requests.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            html (``str``, *optional*):
                HTML-formatted text of the original message.

            markdown (``str``, *optional*):
                Markdown-formatted text of the original message.

            rich_message (:obj:`~pyrogram.types.RichMessage`, *optional*):
                The original rich message.

            tone (:obj:`~pyrogram.types.AiComposeTone` | ``str``, *optional*):
                Tone to rewrite the message with, or the slug of a custom tone.

            custom_prompt (``str``, *optional*):
                A one-time prompt describing how to rewrite (or what to write), used instead of *tone*.

            translate_to_language_code (``str``, *optional*):
                Language code to translate the message to.

            proofread (``bool``, *optional*):
                Pass True to fix spelling and grammar.

            add_emojis (``bool``, *optional*):
                Pass True to add emoji to the message.

        Returns:
            :obj:`~pyrogram.types.RichMessage`: On success, the resulting message is returned.

        Example:
            .. code-block:: python

                draft = await app.compose_rich_message_with_ai(custom_prompt="A short changelog for version 2.0")
                await app.send_rich_message("me", rich_message=draft)
        """
        if tone is not None and custom_prompt is not None:
            raise ValueError("Pass either tone or custom_prompt, not both")

        has_input = any(x is not None for x in (html, markdown, rich_message))

        input_tone = (
            raw.types.InputAiComposeToneSingleUse(custom_prompt=custom_prompt)
            if custom_prompt is not None
            else types.AiComposeTone._to_input(tone)
        )

        r = await self.invoke(
            raw.functions.messages.ComposeRichMessageWithAI(
                text=types.RichMessage._build_input(
                    html=html, markdown=markdown, rich_message=rich_message
                ) if has_input else None,
                tone=input_tone,
                translate_to_lang=translate_to_language_code,
                proofread=proofread or None,
                emojify=add_emojis or None
            )
        )

        return types.RichMessage._parse(self, r.result)
