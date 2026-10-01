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

from typing import Union

import pyrogram
from pyrogram import raw, types, utils


class DeletePollOption:
    async def delete_poll_option(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        message_id: int,
        option: Union[int, bytes]
    ) -> Union["types.Poll", bool]:
        """Delete an option from a poll.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            message_id (``int``):
                Identifier of the message containing the poll.

            option (``int`` | ``bytes``):
                0-based index of the option in the poll, or the *data* of a :obj:`~pyrogram.types.PollOption`.

        Returns:
            :obj:`~pyrogram.types.Poll` | ``bool``: On success, the updated poll is returned,
            or True if Telegram didn't return it.

        Example:
            .. code-block:: python

                await app.delete_poll_option(chat_id, message_id, 2)
        """
        if isinstance(option, int):
            message = await self.get_messages(chat_id, message_id)

            if not message or not message.poll:
                raise ValueError("The message doesn't contain a poll")

            option = message.poll.options[option].data

        r = await self.invoke(
            raw.functions.messages.DeletePollAnswer(
                peer=await self.resolve_peer(chat_id),
                msg_id=message_id,
                option=option
            )
        )

        return await utils.parse_poll_from_updates(self, r) or True
