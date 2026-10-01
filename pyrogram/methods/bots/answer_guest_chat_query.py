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

from typing import Union

import pyrogram
from pyrogram import raw, types, utils


class AnswerGuestChatQuery:
    async def answer_guest_chat_query(
        self: "pyrogram.Client",
        query_id: Union[int, str],
        result: "types.InlineQueryResult"
    ) -> str:
        """Answer a message addressed to the bot by username in a chat the bot isn't a member of.

        See :obj:`~pyrogram.types.GuestChatQuery` and :meth:`~pyrogram.Client.on_guest_chat_query`.

        .. include:: /_includes/usable-by/bots.rst

        Parameters:
            query_id (``int`` | ``str``):
                Identifier of the guest chat query.

            result (:obj:`~pyrogram.types.InlineQueryResult`):
                The result to send in reply to the query.

        Returns:
            ``str``: Identifier of the sent inline message, usable with the methods that edit inline messages.

        Example:
            .. code-block:: python

                from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent

                await app.answer_guest_chat_query(
                    query_id,
                    InlineQueryResultArticle("Hello", InputTextMessageContent("Hello there!"))
                )
        """
        r = await self.invoke(
            raw.functions.messages.SetBotGuestChatResult(
                query_id=int(query_id),
                result=await result.write(self)
            )
        )

        return utils.pack_inline_message_id(r)
