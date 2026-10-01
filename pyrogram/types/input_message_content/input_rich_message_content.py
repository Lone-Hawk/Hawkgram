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

from typing import Optional

import pyrogram
from pyrogram import raw, types

from .input_message_content import InputMessageContent


class InputRichMessageContent(InputMessageContent):
    """Content of a rich message to be sent as the result of an inline query.

    Pass exactly one of *html*, *markdown* or *rich_message*.

    Parameters:
        html (``str``, *optional*):
            HTML-formatted text of the rich message.

        markdown (``str``, *optional*):
            Markdown-formatted text of the rich message.

        rich_message (:obj:`~pyrogram.types.RichMessage`, *optional*):
            An existing rich message, for example one returned by :meth:`~pyrogram.Client.translate_rich_message`.

        is_rtl (``bool``, *optional*):
            Pass True to show the message from right to left.

        disable_auto_links (``bool``, *optional*):
            Pass True to disable automatic detection of links, email addresses and similar entities.
    """

    def __init__(
        self,
        html: Optional[str] = None,
        markdown: Optional[str] = None,
        rich_message: Optional["types.RichMessage"] = None,
        is_rtl: Optional[bool] = None,
        disable_auto_links: Optional[bool] = None
    ):
        super().__init__()

        self.html = html
        self.markdown = markdown
        self.rich_message = rich_message
        self.is_rtl = is_rtl
        self.disable_auto_links = disable_auto_links

    async def write(self, client: "pyrogram.Client", reply_markup):
        return raw.types.InputBotInlineMessageRichMessage(
            rich_message=types.RichMessage._build_input(
                html=self.html,
                markdown=self.markdown,
                rich_message=self.rich_message,
                is_rtl=self.is_rtl,
                disable_auto_links=self.disable_auto_links
            ),
            reply_markup=await reply_markup.write(client) if reply_markup else None
        )
