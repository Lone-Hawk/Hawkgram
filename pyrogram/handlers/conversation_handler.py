#  Hawkgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#  Copyright (C) 2022-present Mayuri-Chan <https://github.com/Mayuri-Chan>
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

import inspect
from typing import Union

import pyrogram
from pyrogram.types import Message, CallbackQuery
from .message_handler import MessageHandler
from .callback_query_handler import CallbackQueryHandler


class ConversationHandler(MessageHandler, CallbackQueryHandler):
    """The Conversation handler class."""
    def __init__(self):
        # Chat id -> waiters, oldest first. A chat used to have a single waiter: waiting again in the same chat (e.g. two
        # users answering a bot at once) replaced the first one, which then never got its answer.
        self.waiters = {}

    def add_waiter(self, chat_id: int, waiter: dict):
        self.waiters.setdefault(chat_id, []).append(waiter)

    async def check(self, client: "pyrogram.Client", update: Union[Message, CallbackQuery]):
        if isinstance(update, Message) and update.outgoing:
            return False

        try:
            chat_id = update.chat.id if isinstance(update, Message) else update.message.chat.id
        except AttributeError:
            return False

        from_user_id = update.from_user.id if update.from_user else None

        for waiter in list(self.waiters.get(chat_id, [])):
            if not isinstance(update, waiter['update_type']) or waiter['future'].done():
                continue

            # A waiter for one user's answer is only given that user's updates, not those of anyone else in the chat
            if waiter.get('user_id') is not None and waiter['user_id'] != from_user_id:
                continue

            filters = waiter.get('filters')
            if callable(filters):
                if inspect.iscoroutinefunction(filters.__call__):
                    filtered = await filters(client, update)
                else:
                    filtered = await client.loop.run_in_executor(
                        client.executor,
                        filters,
                        client, update
                    )
                if not filtered or waiter['future'].done():
                    continue

            waiter['future'].set_result(update)
            return True

        return False

    @staticmethod
    # pylint: disable=method-hidden
    async def callback(_, __):
        pass

    def delete_waiter(self, chat_id, future):
        waiters = [waiter for waiter in self.waiters.get(chat_id, []) if waiter['future'] is not future]

        if waiters:
            self.waiters[chat_id] = waiters
        else:
            self.waiters.pop(chat_id, None)