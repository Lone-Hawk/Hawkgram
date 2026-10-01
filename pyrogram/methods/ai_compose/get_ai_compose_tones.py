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

from typing import List

import pyrogram
from pyrogram import raw, types


class GetAiComposeTones:
    async def get_ai_compose_tones(
        self: "pyrogram.Client"
    ) -> List["types.AiComposeTone"]:
        """Get the AI compose tones available to the current user: the built-in tones and the saved custom tones.

        .. include:: /_includes/usable-by/users.rst

        Returns:
            List of :obj:`~pyrogram.types.AiComposeTone`: On success, the list of tones is returned.

        Example:
            .. code-block:: python

                for tone in await app.get_ai_compose_tones():
                    print(tone.name, tone.title)
        """
        r = await self.invoke(raw.functions.aicompose.GetTones(hash=0))

        if not isinstance(r, raw.types.aicompose.Tones):
            return types.List()

        users = {u.id: u for u in r.users}

        return types.List(filter(None, [types.AiComposeTone._parse(self, tone, users) for tone in r.tones]))
