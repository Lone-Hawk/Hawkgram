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


class SendEphemeralMessage:
    async def send_ephemeral_message(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        user_id: Union[int, str],
        text: str,
        parse_mode: Optional["enums.ParseMode"] = None,
        entities: List["types.MessageEntity"] = None,
        reply_markup: "types.InlineKeyboardMarkup" = None,
        reply_to_message_id: int = None,
        reply_to_ephemeral_message_id: int = None,
        message_thread_id: int = None,
        callback_query_id: Union[int, str] = None,
        protect_content: bool = None,
        invert_media: bool = None
    ) -> "types.EphemeralMessage":
        """Send a text message visible only to a single user of a chat.

        Bots can send ephemeral messages to any user of a chat. Users can send ephemeral messages that only a
        bot receives, for example ephemeral bot commands or replies to ephemeral messages of the bot.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the user (or bot) who will receive the message.

            text (``str``):
                Text of the message to be sent.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
                List of special entities that appear in message text, which can be specified instead of *parse_mode*.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An inline keyboard; for bots only.

            reply_to_message_id (``int``, *optional*):
                If the message is a reply, ID of the original (regular) message.

            reply_to_ephemeral_message_id (``int``, *optional*):
                If the message is a reply to an ephemeral message, ID of the original ephemeral message.

            message_thread_id (``int``, *optional*):
                Unique identifier of the forum topic the message is sent to.

            callback_query_id (``int`` | ``str``, *optional*):
                Identifier of the callback query that triggered the message; for bots only.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            invert_media (``bool``, *optional*):
                Pass True to show the link preview above the message text.

        Returns:
            :obj:`~pyrogram.types.EphemeralMessage`: On success, the sent message is returned.

        Example:
            .. code-block:: python

                await app.send_ephemeral_message(chat_id, user_id, "Only you can see this")
        """
        message, entities = (await utils.parse_text_entities(self, text, parse_mode, entities)).values()

        if reply_to_ephemeral_message_id is not None:
            reply_to = raw.types.InputReplyToEphemeralMessage(id=reply_to_ephemeral_message_id)
        else:
            reply_to = await utils.get_reply_to(
                client=self,
                chat_id=chat_id,
                reply_to_message_id=reply_to_message_id,
                message_thread_id=message_thread_id
            )

        r = await self.invoke(
            raw.functions.ephemeral.SendMessage(
                peer=await self.resolve_peer(chat_id),
                receiver_id=utils.get_input_user(await self.resolve_peer(user_id)),
                message=message,
                entities=entities,
                reply_markup=await reply_markup.write(self) if reply_markup else None,
                reply_to=reply_to,
                query_id=int(callback_query_id) if callback_query_id is not None else None,
                noforwards=protect_content or None,
                invert_media=invert_media or None,
                random_id=self.rnd_id()
            )
        )

        return await types.EphemeralMessage._parse_updates(self, r)
