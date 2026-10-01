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
from pyrogram import raw


class AddWebBrowserException:
    async def add_web_browser_exception(
        self: "pyrogram.Client",
        url: str,
        open_external_browser: bool
    ) -> bool:
        """Always open a website in a specific browser, regardless of the default browser settings.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            url (``str``):
                URL of the website.

            open_external_browser (``bool``):
                Pass True to always open the website in an external browser, False to always use the in-app browser.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.add_web_browser_exception("https://example.com", open_external_browser=True)
        """
        await self.invoke(
            raw.functions.account.ToggleWebBrowserSettingsException(
                url=url,
                open_external_browser=open_external_browser
            )
        )

        return True
