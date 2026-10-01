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

from typing import List, Optional, Union

import pyrogram
from pyrogram import enums, raw, types, utils


class EditEphemeralMessage:
    async def edit_ephemeral_message(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        user_id: Union[int, str],
        message_id: int,
        text: Optional[str] = None,
        parse_mode: Optional["enums.ParseMode"] = None,
        entities: List["types.MessageEntity"] = None,
        reply_markup: "types.InlineKeyboardMarkup" = None
    ) -> Union["types.EphemeralMessage", bool]:
        """Edit the text or the reply markup of an ephemeral message sent by the bot.

        .. include:: /_includes/usable-by/bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the user who received the message.

            message_id (``int``):
                Identifier of the ephemeral message.

            text (``str``, *optional*):
                New text of the message. Pass None to edit only the reply markup.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
                List of special entities that appear in message text, which can be specified instead of *parse_mode*.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                The new inline keyboard.

        Returns:
            :obj:`~pyrogram.types.EphemeralMessage` | ``bool``: On success, the edited message is returned,
            or True if Telegram didn't return it.

        Example:
            .. code-block:: python

                await app.edit_ephemeral_message(chat_id, user_id, message_id, "New text")
        """
        message = None

        if text is not None:
            message, entities = (await utils.parse_text_entities(self, text, parse_mode, entities)).values()

        r = await self.invoke(
            raw.functions.ephemeral.EditMessage(
                peer=await self.resolve_peer(chat_id),
                receiver_id=utils.get_input_user(await self.resolve_peer(user_id)),
                id=message_id,
                message=message,
                entities=entities,
                reply_markup=await reply_markup.write(self) if reply_markup else None
            )
        )

        return await types.EphemeralMessage._parse_updates(self, r) or True
