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

from typing import Optional

import pyrogram
from pyrogram import raw, types


class GetWebBrowserSettings:
    async def get_web_browser_settings(
        self: "pyrogram.Client"
    ) -> Optional["types.WebBrowserSettings"]:
        """Get the settings of the browser used to open links.

        .. include:: /_includes/usable-by/users.rst

        Returns:
            :obj:`~pyrogram.types.WebBrowserSettings`: On success, the settings are returned.

        Example:
            .. code-block:: python

                settings = await app.get_web_browser_settings()
        """
        r = await self.invoke(raw.functions.account.GetWebBrowserSettings(hash=0))

        if not isinstance(r, raw.types.account.WebBrowserSettings):
            return None

        return types.WebBrowserSettings._parse(self, r)
