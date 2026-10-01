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


class EditAiComposeTone:
    async def edit_ai_compose_tone(
        self: "pyrogram.Client",
        tone: Union["types.AiComposeTone", str],
        title: Optional[str] = None,
        prompt: Optional[str] = None,
        custom_emoji_id: Optional[int] = None,
        show_author: Optional[bool] = None
    ) -> "types.AiComposeTone":
        """Edit a custom AI compose tone created by the current user. Only the passed fields are changed.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            tone (:obj:`~pyrogram.types.AiComposeTone` | ``str``):
                The tone, or its slug.

            title (``str``, *optional*):
                New title of the tone.

            prompt (``str``, *optional*):
                New prompt of the tone.

            custom_emoji_id (``int``, *optional*):
                Identifier of the new custom emoji shown for the tone.

            show_author (``bool``, *optional*):
                Pass True to show the current user as the author of the tone, False to hide it.

        Returns:
            :obj:`~pyrogram.types.AiComposeTone`: On success, the edited tone is returned.

        Example:
            .. code-block:: python

                await app.edit_ai_compose_tone(tone, prompt="Rewrite the text like a friendly pirate")
        """
        r = await self.invoke(
            raw.functions.aicompose.UpdateTone(
                tone=types.AiComposeTone._to_input(tone),
                title=title,
                prompt=prompt,
                emoji_id=custom_emoji_id,
                display_author=show_author
            )
        )

        return types.AiComposeTone._parse(self, r)
