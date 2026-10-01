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

from datetime import datetime
from typing import Optional, Union

import pyrogram
from pyrogram import raw, types, utils


class SendRichMessage:
    async def send_rich_message(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        html: Optional[str] = None,
        markdown: Optional[str] = None,
        rich_message: Optional["types.RichMessage"] = None,
        is_rtl: Optional[bool] = None,
        disable_auto_links: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        message_thread_id: Optional[int] = None,
        reply_to_message_id: Optional[int] = None,
        schedule_date: Optional[datetime] = None,
        protect_content: Optional[bool] = None,
        reply_markup: Union[
            "types.InlineKeyboardMarkup",
            "types.ReplyKeyboardMarkup",
            "types.ReplyKeyboardRemove",
            "types.ForceReply"
        ] = None
    ) -> "types.Message":
        """Send a rich message with headings, lists, tables, quotes, formulas and other rich formatting.

        Pass exactly one of *html*, *markdown* or *rich_message*.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            html (``str``, *optional*):
                HTML-formatted text of the message.

            markdown (``str``, *optional*):
                Markdown-formatted text of the message.

            rich_message (:obj:`~pyrogram.types.RichMessage`, *optional*):
                An existing rich message, for example one returned by :meth:`~pyrogram.Client.translate_rich_message`
                or :meth:`~pyrogram.Client.compose_rich_message_with_ai`.

            is_rtl (``bool``, *optional*):
                Pass True to show the message from right to left.

            disable_auto_links (``bool``, *optional*):
                Pass True to disable automatic detection of links, email addresses and similar entities.

            disable_notification (``bool``, *optional*):
                Sends the message silently. Users will receive a notification with no sound.

            message_thread_id (``int``, *optional*):
                Unique identifier of the forum topic the message is sent to.

            reply_to_message_id (``int``, *optional*):
                If the message is a reply, ID of the original message.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the sent message is returned.

        Example:
            .. code-block:: python

                await app.send_rich_message("me", html="<h1>Release notes</h1><ul><li>Faster</li><li>Smaller</li></ul>")
                await app.send_rich_message("me", markdown="# Release notes\n\n- Faster\n- Smaller")
        """
        reply_to = await utils.get_reply_to(
            client=self,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            message_thread_id=message_thread_id
        )

        r = await self.invoke(
            raw.functions.messages.SendMessage(
                peer=await self.resolve_peer(chat_id),
                message="",
                rich_message=types.RichMessage._build_input(
                    html=html,
                    markdown=markdown,
                    rich_message=rich_message,
                    is_rtl=is_rtl,
                    disable_auto_links=disable_auto_links
                ),
                reply_to=reply_to,
                random_id=self.rnd_id(),
                silent=disable_notification or None,
                schedule_date=utils.datetime_to_timestamp(schedule_date),
                noforwards=protect_content or None,
                reply_markup=await reply_markup.write(self) if reply_markup else None
            )
        )

        return await utils.parse_message_from_updates(self, r)
