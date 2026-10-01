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

import pyrogram
from pyrogram import raw, types


class SetWebBrowserSettings:
    async def set_web_browser_settings(
        self: "pyrogram.Client",
        open_external_browser: bool,
        show_close_button: bool = False
    ) -> "types.WebBrowserSettings":
        """Change the settings of the browser used to open links.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            open_external_browser (``bool``):
                Pass True to open links in an external browser by default, False to use the in-app browser.

            show_close_button (``bool``, *optional*):
                Pass True to show a close button in the in-app browser (Android only).

        Returns:
            :obj:`~pyrogram.types.WebBrowserSettings`: On success, the new settings are returned.

        Example:
            .. code-block:: python

                await app.set_web_browser_settings(open_external_browser=True)
        """
        r = await self.invoke(
            raw.functions.account.UpdateWebBrowserSettings(
                open_external_browser=open_external_browser or None,
                display_close_button=show_close_button or None
            )
        )

        return types.WebBrowserSettings._parse(self, r)
