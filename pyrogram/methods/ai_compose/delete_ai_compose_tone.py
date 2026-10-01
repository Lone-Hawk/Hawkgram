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


class DeleteAiComposeTone:
    async def delete_ai_compose_tone(
        self: "pyrogram.Client",
        tone: Union["types.AiComposeTone", str]
    ) -> bool:
        """Delete a custom AI compose tone created by the current user.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            tone (:obj:`~pyrogram.types.AiComposeTone` | ``str``):
                The tone, or its slug.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.delete_ai_compose_tone(tone)
        """
        return await self.invoke(
            raw.functions.aicompose.DeleteTone(tone=types.AiComposeTone._to_input(tone))
        )
