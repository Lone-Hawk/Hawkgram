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


class GetAiComposeToneExample:
    async def get_ai_compose_tone_example(
        self: "pyrogram.Client",
        tone: Union["types.AiComposeTone", str],
        example_number: int = 0
    ) -> "types.AiComposeToneExample":
        """Get an example of a text before and after applying an AI compose tone.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            tone (:obj:`~pyrogram.types.AiComposeTone` | ``str``):
                The tone, or the slug of a custom tone.

            example_number (``int``, *optional*):
                0-based number of the example. Defaults to 0.

        Returns:
            :obj:`~pyrogram.types.AiComposeToneExample`: On success, the example is returned.

        Example:
            .. code-block:: python

                example = await app.get_ai_compose_tone_example("pirate")
                print(example.text, "->", example.result_text)
        """
        r = await self.invoke(
            raw.functions.aicompose.GetToneExample(tone=types.AiComposeTone._to_input(tone), num=example_number)
        )

        return types.AiComposeToneExample._parse(self, r)
