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

from typing import Optional, Union

import pyrogram
from pyrogram import raw, types


class GetAiComposeTone:
    async def get_ai_compose_tone(
        self: "pyrogram.Client",
        tone: Union["types.AiComposeTone", str]
    ) -> Optional["types.AiComposeTone"]:
        """Get an AI compose tone, for example a custom tone shared by another user.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            tone (:obj:`~pyrogram.types.AiComposeTone` | ``str``):
                The tone, or the slug of a custom tone.

        Returns:
            :obj:`~pyrogram.types.AiComposeTone`: On success, the tone is returned.

        Example:
            .. code-block:: python

                tone = await app.get_ai_compose_tone("pirate")
        """
        r = await self.invoke(
            raw.functions.aicompose.GetTone(tone=types.AiComposeTone._to_input(tone))
        )

        if not isinstance(r, raw.types.aicompose.Tones) or not r.tones:
            return None

        return types.AiComposeTone._parse(self, r.tones[0], {u.id: u for u in r.users})
