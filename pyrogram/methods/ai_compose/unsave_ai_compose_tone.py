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
from pyrogram import raw, types


class UnsaveAiComposeTone:
    async def unsave_ai_compose_tone(
        self: "pyrogram.Client",
        tone: Union["types.AiComposeTone", str]
    ) -> bool:
        """Remove a custom AI compose tone from the tones of the current user.

        Tones created by the current user can't be removed; use :meth:`~pyrogram.Client.delete_ai_compose_tone`.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            tone (:obj:`~pyrogram.types.AiComposeTone` | ``str``):
                The tone, or its slug.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.unsave_ai_compose_tone("pirate")
        """
        return await self.invoke(
            raw.functions.aicompose.SaveTone(tone=types.AiComposeTone._to_input(tone), unsave=True)
        )
