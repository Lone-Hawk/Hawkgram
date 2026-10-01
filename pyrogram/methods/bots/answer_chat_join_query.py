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
from pyrogram import enums, raw


class AnswerChatJoinQuery:
    async def answer_chat_join_query(
        self: "pyrogram.Client",
        query_id: Union[int, str],
        result: Optional["enums.ChatJoinQueryResult"] = None,
        web_app_url: Optional[str] = None
    ) -> bool:
        """Answer a request to join a chat protected by the bot as its guard bot.

        The query identifier is available in :obj:`~pyrogram.types.ChatJoinRequest.query_id`.
        Pass exactly one of *result* or *web_app_url*.

        .. include:: /_includes/usable-by/bots.rst

        Parameters:
            query_id (``int`` | ``str``):
                Identifier of the join query.

            result (:obj:`~pyrogram.enums.ChatJoinQueryResult`, *optional*):
                The decision about the request.

            web_app_url (``str``, *optional*):
                URL of a Web App the user must open to continue, for example to solve a challenge.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                from pyrogram import enums

                @app.on_chat_join_request()
                async def guard(client, request):
                    if request.query_id:
                        await client.answer_chat_join_query(request.query_id, enums.ChatJoinQueryResult.APPROVED)
        """
        if (result is None) == (web_app_url is None):
            raise ValueError("Pass exactly one of result or web_app_url")

        if web_app_url is not None:
            join_result = raw.types.JoinChatBotResultWebView(url=web_app_url)
        elif result == enums.ChatJoinQueryResult.APPROVED:
            join_result = raw.types.JoinChatBotResultApproved()
        elif result == enums.ChatJoinQueryResult.DECLINED:
            join_result = raw.types.JoinChatBotResultDeclined()
        else:
            join_result = raw.types.JoinChatBotResultQueued()

        return await self.invoke(
            raw.functions.bots.SetJoinChatResults(query_id=int(query_id), result=join_result)
        )
