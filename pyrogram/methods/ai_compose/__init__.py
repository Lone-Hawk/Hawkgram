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

from .compose_text_with_ai import ComposeTextWithAi
from .create_ai_compose_tone import CreateAiComposeTone
from .delete_ai_compose_tone import DeleteAiComposeTone
from .edit_ai_compose_tone import EditAiComposeTone
from .get_ai_compose_tone import GetAiComposeTone
from .get_ai_compose_tone_example import GetAiComposeToneExample
from .get_ai_compose_tones import GetAiComposeTones
from .save_ai_compose_tone import SaveAiComposeTone
from .unsave_ai_compose_tone import UnsaveAiComposeTone


class AiCompose(
    ComposeTextWithAi,
    CreateAiComposeTone,
    DeleteAiComposeTone,
    EditAiComposeTone,
    GetAiComposeTone,
    GetAiComposeToneExample,
    GetAiComposeTones,
    SaveAiComposeTone,
    UnsaveAiComposeTone,
):
    pass
