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

from typing import Optional, Union

import pyrogram
from pyrogram import raw, types, utils


class EditRichMessage:
    async def edit_rich_message(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        message_id: int,
        html: Optional[str] = None,
        markdown: Optional[str] = None,
        rich_message: Optional["types.RichMessage"] = None,
        is_rtl: Optional[bool] = None,
        disable_auto_links: Optional[bool] = None,
        reply_markup: "types.InlineKeyboardMarkup" = None
    ) -> "types.Message":
        """Edit a rich message.

        Pass exactly one of *html*, *markdown* or *rich_message*.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            message_id (``int``):
                Identifier of the message to edit.

            html (``str``, *optional*):
                New HTML-formatted text of the message.

            markdown (``str``, *optional*):
                New Markdown-formatted text of the message.

            rich_message (:obj:`~pyrogram.types.RichMessage`, *optional*):
                The new rich message.

            is_rtl (``bool``, *optional*):
                Pass True to show the message from right to left.

            disable_auto_links (``bool``, *optional*):
                Pass True to disable automatic detection of links, email addresses and similar entities.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An inline keyboard.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the edited message is returned.

        Example:
            .. code-block:: python

                await app.edit_rich_message(chat_id, message_id, markdown="# Updated notes")
        """
        r = await self.invoke(
            raw.functions.messages.EditMessage(
                peer=await self.resolve_peer(chat_id),
                id=message_id,
                rich_message=types.RichMessage._build_input(
                    html=html,
                    markdown=markdown,
                    rich_message=rich_message,
                    is_rtl=is_rtl,
                    disable_auto_links=disable_auto_links
                ),
                reply_markup=await reply_markup.write(self) if reply_markup else None
            )
        )

        return await utils.parse_message_from_updates(self, r)
