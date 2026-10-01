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

from typing import Dict, List, Optional, Tuple, Union

import pyrogram
from pyrogram import enums, raw, types, utils

from .message import Message


class EphemeralMessage(Message):
    """A message visible only to a single user of a chat.

    Bots can send ephemeral messages to a user in a group, and users can send ephemeral messages (for example
    ephemeral bot commands) that only the bot receives. Ephemeral messages have the same content as regular
    messages (text, media, keyboards, ...), so all the fields of :obj:`~pyrogram.types.Message` are available,
    plus the ones listed below.

    The bound methods :meth:`edit_text`, :meth:`edit_reply_markup`, :meth:`delete` and :meth:`reply` act on the
    ephemeral message. Other bound methods of :obj:`~pyrogram.types.Message` are meant for regular messages and
    don't apply to ephemeral messages.

    Parameters:
        receiver_user_id (``int``):
            Identifier of the user who receives the message.

        is_welcome_template (``bool``, *optional*):
            True, if the message is a welcome message that is shown to users joining the chat.

        chat_instance (``int``, *optional*):
            Identifier that uniquely corresponds to the chat of the message; for bots only.
    """

    receiver_user_id: int = None
    is_welcome_template: bool = None
    chat_instance: int = None

    @staticmethod
    async def _parse_ephemeral(
        client: "pyrogram.Client",
        ephemeral: "raw.types.EphemeralMessage",
        users: Dict[int, "raw.types.User"],
        chats: Dict[int, "raw.types.Chat"]
    ) -> "EphemeralMessage":
        peer_id = ephemeral.peer_id

        if peer_id is None:
            peer_id = raw.types.PeerUser(user_id=ephemeral.receiver_id) if ephemeral.out else ephemeral.from_id

        from_id = ephemeral.from_id

        # Some responses (e.g. the list of welcome messages) don't include the chat or the sender,
        # which the message parser needs, so they are fetched when missing
        for peer in (peer_id, from_id):
            if peer is None:
                continue

            known = users if isinstance(peer, raw.types.PeerUser) else chats

            if utils.get_raw_peer_id(peer) not in known:
                try:
                    fetched_users, fetched_chats = await EphemeralMessage._fetch_peers(client, utils.get_peer_id(peer))
                except Exception:
                    # The chat is required to parse the message, the sender is not
                    if peer is peer_id:
                        raise

                    continue

                users = {**users, **fetched_users}
                chats = {**chats, **fetched_chats}

        # A sender that still couldn't be found is left out rather than failing the whole message
        if from_id is not None:
            known = users if isinstance(from_id, raw.types.PeerUser) else chats

            if utils.get_raw_peer_id(from_id) not in known:
                from_id = None

        # Ephemeral messages carry the same content as regular messages, so the regular message parser is reused.
        # Replies aren't fetched and the result isn't cached, since ephemeral identifiers are a separate id space.
        message = raw.types.Message(
            id=ephemeral.id,
            peer_id=peer_id,
            date=ephemeral.date,
            message=ephemeral.message,
            out=ephemeral.out,
            noforwards=ephemeral.noforwards,
            invert_media=ephemeral.invert_media,
            from_id=from_id,
            entities=ephemeral.entities,
            media=ephemeral.media,
            reply_markup=ephemeral.reply_markup,
            reply_to=ephemeral.reply_to,
            rich_message=ephemeral.rich_message
        )

        parsed = await Message._parse(client, message, users, chats, replies=0, cache=False)
        parsed.__class__ = EphemeralMessage
        parsed.receiver_user_id = ephemeral.receiver_id or None
        parsed.is_welcome_template = ephemeral.welcome_template
        parsed.chat_instance = ephemeral.chat_instance

        if ephemeral.top_msg_id:
            parsed.message_thread_id = ephemeral.top_msg_id

        parsed.raw = ephemeral

        return parsed

    @staticmethod
    async def _parse_updates(
        client: "pyrogram.Client",
        updates: "raw.base.Updates"
    ) -> Optional["EphemeralMessage"]:
        """Return the ephemeral message contained in the result of a send or edit request, if any."""
        users = {u.id: u for u in getattr(updates, "users", [])}
        chats = {c.id: c for c in getattr(updates, "chats", [])}

        for update in getattr(updates, "updates", []):
            if isinstance(update, (raw.types.UpdateNewEphemeralMessage, raw.types.UpdateEditEphemeralMessage)):
                return await EphemeralMessage._parse_ephemeral(client, update.message, users, chats)

        return None

    @staticmethod
    async def _fetch_peers(
        client: "pyrogram.Client",
        chat_id: Union[int, str]
    ) -> Tuple[Dict[int, "raw.types.User"], Dict[int, "raw.types.Chat"]]:
        """Fetch the raw user and chat objects for *chat_id*, for responses that don't include them."""
        peer = await client.resolve_peer(chat_id)

        if isinstance(peer, raw.types.InputPeerChannel):
            r = await client.invoke(raw.functions.channels.GetChannels(id=[utils.get_input_channel(peer)]))
            return {}, {c.id: c for c in r.chats}

        if isinstance(peer, raw.types.InputPeerChat):
            r = await client.invoke(raw.functions.messages.GetChats(id=[peer.chat_id]))
            return {}, {c.id: c for c in r.chats}

        r = await client.invoke(raw.functions.users.GetUsers(id=[utils.get_input_user(peer)]))
        return {u.id: u for u in r}, {}

    @property
    def _other_user_id(self) -> Optional[int]:
        """The user on the other side of this ephemeral conversation."""
        if self.outgoing:
            return self.receiver_user_id

        return self.from_user.id if self.from_user else None

    async def edit_text(
        self,
        text: str,
        parse_mode: Optional["enums.ParseMode"] = None,
        entities: List["types.MessageEntity"] = None,
        reply_markup: "types.InlineKeyboardMarkup" = None
    ) -> "EphemeralMessage":
        """Bound method *edit_text* of :obj:`~pyrogram.types.EphemeralMessage`.

        Use as a shortcut for :meth:`~pyrogram.Client.edit_ephemeral_message`.

        Example:
            .. code-block:: python

                await message.edit_text("new text")
        """
        return await self._client.edit_ephemeral_message(
            chat_id=self.chat.id,
            user_id=self.receiver_user_id,
            message_id=self.id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            reply_markup=reply_markup
        )

    edit = edit_text

    async def edit_reply_markup(self, reply_markup: "types.InlineKeyboardMarkup" = None) -> "EphemeralMessage":
        """Bound method *edit_reply_markup* of :obj:`~pyrogram.types.EphemeralMessage`.

        Use as a shortcut for :meth:`~pyrogram.Client.edit_ephemeral_message` with only a reply markup.

        Example:
            .. code-block:: python

                await message.edit_reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton("Hi", callback_data="hi")]]))
        """
        return await self._client.edit_ephemeral_message(
            chat_id=self.chat.id,
            user_id=self.receiver_user_id,
            message_id=self.id,
            reply_markup=reply_markup
        )

    async def delete(self, revoke: bool = True) -> bool:
        """Bound method *delete* of :obj:`~pyrogram.types.EphemeralMessage`.

        Use as a shortcut for :meth:`~pyrogram.Client.delete_ephemeral_message`.

        Parameters:
            revoke (``bool``, *optional*):
                Ignored; ephemeral messages are always deleted for their receiver.

        Example:
            .. code-block:: python

                await message.delete()
        """
        return await self._client.delete_ephemeral_message(
            chat_id=self.chat.id,
            user_id=self.receiver_user_id,
            message_id=self.id
        )

    async def reply_text(
        self,
        text: str,
        parse_mode: Optional["enums.ParseMode"] = None,
        entities: List["types.MessageEntity"] = None,
        reply_markup: "types.InlineKeyboardMarkup" = None,
        quote: bool = True,
        protect_content: bool = None
    ) -> "EphemeralMessage":
        """Bound method *reply_text* of :obj:`~pyrogram.types.EphemeralMessage`.

        Replies with another ephemeral message, visible only to the other side of this ephemeral conversation.
        Use as a shortcut for :meth:`~pyrogram.Client.send_ephemeral_message`.

        Parameters:
            text (``str``):
                Text of the message to be sent.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.

            entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
                List of special entities that appear in message text, which can be specified instead of *parse_mode*.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An inline keyboard.

            quote (``bool``, *optional*):
                If True, the new message is sent as a reply to this message. Defaults to True.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

        Example:
            .. code-block:: python

                await message.reply("Only you can see this")
        """
        return await self._client.send_ephemeral_message(
            chat_id=self.chat.id,
            user_id=self._other_user_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            reply_markup=reply_markup,
            reply_to_ephemeral_message_id=self.id if quote else None,
            message_thread_id=self.message_thread_id,
            protect_content=protect_content
        )

    reply = reply_text
