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

from pyrogram import raw

from ..object import Object


class WebDomainException(Object):
    """A website that is always opened in a specific browser.

    Parameters:
        domain (``str``):
            Domain of the website.

        url (``str``):
            URL of the website.

        title (``str``):
            Title of the website.

        favicon_custom_emoji_id (``int``, *optional*):
            Identifier of the custom emoji used as favicon of the website.
    """

    def __init__(
        self,
        *,
        domain: str,
        url: str,
        title: str,
        favicon_custom_emoji_id: Optional[int] = None
    ):
        super().__init__()

        self.domain = domain
        self.url = url
        self.title = title
        self.favicon_custom_emoji_id = favicon_custom_emoji_id

    @staticmethod
    def _parse(exception: "raw.types.WebDomainException") -> "WebDomainException":
        return WebDomainException(
            domain=exception.domain,
            url=exception.url,
            title=exception.title,
            favicon_custom_emoji_id=exception.favicon
        )
