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

from typing import Union

import pyrogram
from pyrogram import raw
from pyrogram import types


class JoinChat:
    async def join_chat(
        self: "pyrogram.Client",
        chat_id: Union[int, str]
    ) -> "types.Chat":
        """Join a group chat or channel.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier for the target chat in form of a *t.me/joinchat/* or *t.me/<username>* link,
                a username of the target channel/supergroup (in the format @username) or a chat id of a linked chat (channel or supergroup).

        Returns:
            :obj:`~pyrogram.types.Chat` | ``None``: On success, a chat object is returned.
            ``None`` is returned in case the join must first be approved by the chat's guard bot.

        Example:
            .. code-block:: python

                # Join chat via invite link
                await app.join_chat("https://t.me/+AbCdEf0123456789")

                # Join chat via username
                await app.join_chat("pyrogram")

                # Join a linked chat
                await app.join_chat(app.get_chat("pyrogram").linked_chat.id)
        """
        match = self.INVITE_LINK_RE.match(str(chat_id))

        if match:
            r = await self.invoke(
                raw.functions.messages.ImportChatInvite(
                    hash=match.group(1)
                )
            )
        else:
            r = await self.invoke(
                raw.functions.channels.JoinChannel(
                    channel=await self.resolve_peer(chat_id)
                )
            )

        # The join is pending approval by the chat's guard bot
        if not isinstance(r, raw.types.messages.ChatInviteJoinResultOk):
            return None

        await self.fetch_peers(r.updates.users)
        await self.fetch_peers(r.updates.chats)

        chat = r.updates.chats[0]

        if isinstance(chat, raw.types.Chat):
            return types.Chat._parse_chat_chat(self, chat)
        elif isinstance(chat, raw.types.Channel):
            return types.Chat._parse_channel_chat(self, chat)
