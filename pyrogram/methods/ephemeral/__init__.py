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

from .add_welcome_message import AddWelcomeMessage
from .delete_all_welcome_messages import DeleteAllWelcomeMessages
from .delete_ephemeral_message import DeleteEphemeralMessage
from .delete_welcome_message import DeleteWelcomeMessage
from .edit_ephemeral_message import EditEphemeralMessage
from .edit_welcome_message import EditWelcomeMessage
from .get_welcome_messages import GetWelcomeMessages
from .request_ephemeral_callback_answer import RequestEphemeralCallbackAnswer
from .send_ephemeral_message import SendEphemeralMessage


class EphemeralMessages(
    AddWelcomeMessage,
    DeleteAllWelcomeMessages,
    DeleteEphemeralMessage,
    DeleteWelcomeMessage,
    EditEphemeralMessage,
    EditWelcomeMessage,
    GetWelcomeMessages,
    RequestEphemeralCallbackAnswer,
    SendEphemeralMessage,
):
    pass
