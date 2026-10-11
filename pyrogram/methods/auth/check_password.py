#  Hawkgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#  Copyright (C) 2022-present Mayuri-Chan <https://github.com/Mayuri-Chan>
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

import logging

import pyrogram
from pyrogram import raw
from pyrogram import types
from pyrogram.utils import compute_password_check, run_sync

log = logging.getLogger(__name__)


class CheckPassword:
    async def check_password(
        self: "pyrogram.Client",
        password: str
    ) -> "types.User":
        """Check your Two-Step Verification password and log in.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            password (``str``):
                Your Two-Step Verification password.

        Returns:
            :obj:`~pyrogram.types.User`: On success, the authorized user is returned.

        Raises:
            BadRequest: In case the password is invalid.
        """
        # Hashing the password (100000 PBKDF2 rounds) runs in a thread, not on the event loop it would block
        password_check = await run_sync(
            compute_password_check,
            await self.invoke(raw.functions.account.GetPassword()),
            password
        )

        r = await self.invoke(
            raw.functions.auth.CheckPassword(
                password=password_check
            )
        )

        await self.storage.user_id(r.user.id)
        await self.storage.is_bot(False)

        return types.User._parse(self, r.user)
