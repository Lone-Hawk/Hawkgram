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
from pyrogram import raw, types


class CreateAiComposeTone:
    async def create_ai_compose_tone(
        self: "pyrogram.Client",
        title: str,
        prompt: str,
        custom_emoji_id: int,
        show_author: bool = False
    ) -> "types.AiComposeTone":
        """Create a custom AI compose tone.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            title (``str``):
                Title of the tone.

            prompt (``str``):
                Prompt describing how texts must be rewritten.

            custom_emoji_id (``int``):
                Identifier of the custom emoji shown for the tone.

            show_author (``bool``, *optional*):
                Pass True to show the current user as the author of the tone.

        Returns:
            :obj:`~pyrogram.types.AiComposeTone`: On success, the created tone is returned.

        Example:
            .. code-block:: python

                tone = await app.create_ai_compose_tone("Pirate", "Rewrite the text like a pirate", 5368324170671202286)
        """
        r = await self.invoke(
            raw.functions.aicompose.CreateTone(
                title=title,
                prompt=prompt,
                emoji_id=custom_emoji_id,
                display_author=show_author or None
            )
        )

        return types.AiComposeTone._parse(self, r)
