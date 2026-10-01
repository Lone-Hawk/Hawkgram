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

from typing import Callable

from pyrogram.filters import Filter
from .deleted_messages_handler import DeletedMessagesHandler


class DeletedEphemeralMessagesHandler(DeletedMessagesHandler):
    """The deleted ephemeral messages handler class. Used to handle deleted ephemeral messages.
    It is intended to be used with :meth:`~pyrogram.Client.add_handler`

    For a nicer way to register this handler, have a look at the
    :meth:`~pyrogram.Client.on_deleted_ephemeral_messages` decorator.

    Parameters:
        callback (``Callable``):
            Pass a function that will be called when one or more ephemeral messages have been deleted.
            It takes *(client, messages)* as positional arguments (look at the section below for a detailed description).

        filters (:obj:`Filters`):
            Pass one or more filters to allow only a subset of messages to be passed
            in your callback function.

    Other parameters:
        client (:obj:`~pyrogram.Client`):
            The Client itself, useful when you want to call other API methods inside the message handler.

        messages (List of :obj:`~pyrogram.types.EphemeralMessage`):
            The deleted ephemeral messages, as list. Only their *id* and *chat* are known.
    """

    def __init__(self, callback: Callable, filters: Filter = None):
        super().__init__(callback, filters)
