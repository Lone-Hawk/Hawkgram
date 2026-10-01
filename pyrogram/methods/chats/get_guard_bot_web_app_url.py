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

from typing import Union

import pyrogram
from pyrogram import raw


class GetGuardBotWebAppUrl:
    async def get_guard_bot_web_app_url(
        self: "pyrogram.Client",
        query_id: Union[int, str],
        platform: str = "android"
    ) -> str:
        """Get the URL of the Web App a user must open to be let into a chat protected by a guard bot.

        Needed after :meth:`~pyrogram.Client.join_chat` returned None because the guard bot must approve the join.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            query_id (``int`` | ``str``):
                Identifier of the join request received from Telegram.

            platform (``str``, *optional*):
                Short name of the platform the Web App is opened on, e.g. "android", "ios", "tdesktop" or "web".
                Defaults to "android".

        Returns:
            ``str``: On success, the URL of the Web App is returned.

        Example:
            .. code-block:: python

                url = await app.get_guard_bot_web_app_url(query_id)
        """
        r = await self.invoke(
            raw.functions.messages.RequestChatJoinWebView(
                query_id=int(query_id),
                platform=platform
            )
        )

        return r.url
