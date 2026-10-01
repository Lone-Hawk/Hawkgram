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


class AddPollOption:
    async def add_poll_option(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        message_id: int,
        text: str,
        parse_mode: Optional["enums.ParseMode"] = None,
        entities: List["types.MessageEntity"] = None
    ) -> Union["types.Poll", bool]:
        """Add an option to a poll that allows adding options.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            message_id (``int``):
                Identifier of the message containing the poll.

            text (``str``):
                Text of the new option, 1-100 characters.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
                Special entities of the option text; only custom emoji are allowed.

        Returns:
            :obj:`~pyrogram.types.Poll` | ``bool``: On success, the updated poll is returned,
            or True if Telegram didn't return it.

        Example:
            .. code-block:: python

                await app.add_poll_option(chat_id, message_id, "Pizza")
        """
        option, entities = (await utils.parse_text_entities(self, text, parse_mode, entities)).values()

        r = await self.invoke(
            raw.functions.messages.AddPollAnswer(
                peer=await self.resolve_peer(chat_id),
                msg_id=message_id,
                answer=raw.types.InputPollAnswer(
                    text=raw.types.TextWithEntities(text=option, entities=entities or [])
                )
            )
        )

        return await utils.parse_poll_from_updates(self, r) or True
