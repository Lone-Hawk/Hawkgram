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

from typing import Dict, List, Optional

import pyrogram
from pyrogram import raw, types

from ..object import Object
from ..update import Update


class GuestChatQuery(Object, Update):
    """A message addressed to the bot by username in a chat the bot isn't a member of.

    Bots that support guest queries receive such messages and answer them with an inline result,
    using :meth:`~pyrogram.Client.answer_guest_chat_query`.

    Parameters:
        id (``str``):
            Unique identifier of the query, used to answer it.

        message (:obj:`~pyrogram.types.Message`):
            The message addressed to the bot.

        reference_messages (List of :obj:`~pyrogram.types.Message`, *optional*):
            Messages referenced by the query, for example the message it replies to.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        id: str,
        message: "types.Message",
        reference_messages: Optional[List["types.Message"]] = None
    ):
        super().__init__(client)

        self.id = id
        self.message = message
        self.reference_messages = reference_messages

    @staticmethod
    async def _parse(
        client: "pyrogram.Client",
        update: "raw.types.UpdateBotGuestChatQuery",
        users: Dict[int, "raw.types.User"],
        chats: Dict[int, "raw.types.Chat"]
    ) -> "GuestChatQuery":
        async def parse(message):
            return await types.Message._parse(client, message, users, chats, replies=0, cache=False)

        reference_messages = [await parse(m) for m in update.reference_messages or []]

        return GuestChatQuery(
            client=client,
            id=str(update.query_id),
            message=await parse(update.message),
            reference_messages=types.List(reference_messages) or None
        )

    async def answer(self, result: "types.InlineQueryResult") -> str:
        """Bound method *answer* of :obj:`~pyrogram.types.GuestChatQuery`.

        Use as a shortcut for :meth:`~pyrogram.Client.answer_guest_chat_query`.

        Parameters:
            result (:obj:`~pyrogram.types.InlineQueryResult`):
                The result to send in reply to the query.

        Returns:
            ``str``: Identifier of the sent inline message, usable with the methods that edit inline messages.

        Example:
            .. code-block:: python

                await query.answer(InlineQueryResultArticle("Hi", InputTextMessageContent("Hello!")))
        """
        return await self._client.answer_guest_chat_query(self.id, result)
