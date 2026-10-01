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


class AddWelcomeMessage:
    async def add_welcome_message(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional["enums.ParseMode"] = None,
        entities: List["types.MessageEntity"] = None
    ) -> "types.EphemeralMessage":
        """Add a welcome message to a chat. Welcome messages are shown privately to users who join the chat.

        Requires administrator rights to manage welcome messages in the chat.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            text (``str``):
                Text of the welcome message.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
                List of special entities that appear in message text, which can be specified instead of *parse_mode*.

        Returns:
            :obj:`~pyrogram.types.EphemeralMessage`: On success, the added welcome message is returned.

        Example:
            .. code-block:: python

                await app.add_welcome_message(chat_id, "Welcome! Please read the pinned rules.")
        """
        message, entities = (await utils.parse_text_entities(self, text, parse_mode, entities)).values()

        r = await self.invoke(
            raw.functions.ephemeral.SendMessage(
                peer=await self.resolve_peer(chat_id),
                receiver_id=raw.types.InputUserEmpty(),
                welcome=True,
                message=message,
                entities=entities,
                random_id=self.rnd_id()
            )
        )

        return await types.EphemeralMessage._parse_updates(self, r)
