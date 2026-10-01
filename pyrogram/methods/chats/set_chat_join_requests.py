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
from pyrogram import raw, utils


class SetChatJoinRequests:
    async def set_chat_join_requests(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        enabled: bool,
        guard_bot_id: Optional[Union[int, str]] = None,
        apply_to_invite_links: bool = False
    ) -> bool:
        """Choose whether users joining a supergroup directly must be approved first.

        Join requests can be reviewed by administrators, or by a guard bot that approves or declines them
        automatically (see :meth:`~pyrogram.Client.answer_chat_join_query`).

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the supergroup.

            enabled (``bool``):
                Pass True to require approval, False to let users join directly.

            guard_bot_id (``int`` | ``str``, *optional*):
                Unique identifier (int) or username (str) of a bot that will handle the join requests.
                The bot must be an administrator of the chat with the right to invite users.

            apply_to_invite_links (``bool``, *optional*):
                Pass True to apply the change to the existing invite links, including the primary one.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.set_chat_join_requests(chat_id, True, guard_bot_id="my_guard_bot")
        """
        guard_bot = None

        if guard_bot_id is not None:
            guard_bot = utils.get_input_user(await self.resolve_peer(guard_bot_id))

        await self.invoke(
            raw.functions.channels.ToggleJoinRequest(
                channel=utils.get_input_channel(await self.resolve_peer(chat_id)),
                enabled=enabled,
                guard_bot=guard_bot,
                apply_to_invites=apply_to_invite_links or None
            )
        )

        return True
