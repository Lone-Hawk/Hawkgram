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

import pyrogram
from pyrogram import raw


class RemoveWebBrowserException:
    async def remove_web_browser_exception(
        self: "pyrogram.Client",
        url: str
    ) -> bool:
        """Stop opening a website in a specific browser, so the default browser settings apply again.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            url (``str``):
                URL of the website.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.remove_web_browser_exception("https://example.com")
        """
        await self.invoke(
            raw.functions.account.ToggleWebBrowserSettingsException(
                url=url,
                delete=True
            )
        )

        return True
