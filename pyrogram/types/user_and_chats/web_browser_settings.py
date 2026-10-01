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

from typing import List, Optional

import pyrogram
from pyrogram import raw, types

from ..object import Object


class WebBrowserSettings(Object):
    """Settings of the browser used to open links.

    Parameters:
        open_external_browser (``bool``):
            True, if links are opened in an external browser by default.

        show_close_button (``bool``):
            True, if a close button is shown in the in-app browser (Android only).

        external_exceptions (List of :obj:`~pyrogram.types.WebDomainException`):
            Websites that are always opened in an external browser.

        in_app_exceptions (List of :obj:`~pyrogram.types.WebDomainException`):
            Websites that are always opened in the in-app browser.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        open_external_browser: bool,
        show_close_button: bool,
        external_exceptions: List["types.WebDomainException"],
        in_app_exceptions: List["types.WebDomainException"]
    ):
        super().__init__(client)

        self.open_external_browser = open_external_browser
        self.show_close_button = show_close_button
        self.external_exceptions = external_exceptions
        self.in_app_exceptions = in_app_exceptions

    @staticmethod
    def _parse(
        client: "pyrogram.Client",
        settings: "raw.types.account.WebBrowserSettings"
    ) -> "WebBrowserSettings":
        return WebBrowserSettings(
            client=client,
            open_external_browser=bool(settings.open_external_browser),
            show_close_button=bool(settings.display_close_button),
            external_exceptions=types.List(types.WebDomainException._parse(e) for e in settings.external_exceptions),
            in_app_exceptions=types.List(types.WebDomainException._parse(e) for e in settings.inapp_exceptions)
        )
