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


class TranslateRichMessage:
    async def translate_rich_message(
        self: "pyrogram.Client",
        to_language_code: str,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        html: Optional[str] = None,
        markdown: Optional[str] = None,
        rich_message: Optional["types.RichMessage"] = None,
        tone: Optional[str] = None
    ) -> "types.RichMessage":
        """Translate a rich message to another language.

        Pass either *chat_id* and *message_id* to translate a sent message, or exactly one of *html*, *markdown* or
        *rich_message* to translate a message that wasn't sent yet.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            to_language_code (``str``):
                Language code of the language to translate the message to.

            chat_id (``int`` | ``str``, *optional*):
                Unique identifier (int) or username (str) of the chat of the message.

            message_id (``int``, *optional*):
                Identifier of the message.

            html (``str``, *optional*):
                HTML-formatted text of the message to translate.

            markdown (``str``, *optional*):
                Markdown-formatted text of the message to translate.

            rich_message (:obj:`~pyrogram.types.RichMessage`, *optional*):
                The rich message to translate.

            tone (``str``, *optional*):
                Name of a built-in AI compose tone for the translation.

        Returns:
            :obj:`~pyrogram.types.RichMessage`: On success, the translated message is returned.

        Example:
            .. code-block:: python

                translated = await app.translate_rich_message("de", chat_id=chat_id, message_id=message_id)
                await app.send_rich_message(chat_id, rich_message=translated)
        """
        if chat_id is not None and message_id is not None:
            r = await self.invoke(
                raw.functions.messages.TranslateRichMessage(
                    peer=await self.resolve_peer(chat_id),
                    id=[message_id],
                    to_lang=to_language_code,
                    tone=tone
                )
            )
        else:
            r = await self.invoke(
                raw.functions.messages.TranslateRichMessage(
                    text=[types.RichMessage._build_input(html=html, markdown=markdown, rich_message=rich_message)],
                    to_lang=to_language_code,
                    tone=tone
                )
            )

        return types.RichMessage._parse(self, r.result[0]) if r.result else None
