#  Hawkgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
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
from pyrogram import errors, raw, utils


class TransferGift:
    async def transfer_gift(
        self: "pyrogram.Client",
        message_id: int,
        to_chat_id: Union[int, str],
        max_star_count: Optional[int] = None
    ) -> bool:
        """Transfer star gift to another user.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            message_id (``int``):
                Unique message identifier of star gift.

            to_chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat you want to transfer the star gift to.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            max_star_count (``int``, *optional*):
                The most Telegram Stars you agree to pay if the transfer isn't free.
                By default nothing is paid: :obj:`~pyrogram.errors.PaymentRequired` is raised when the transfer
                costs Stars. If it costs more than *max_star_count*, ``ValueError`` is raised and nothing is paid.

        Returns:
            ``bool``: On success, True is returned.

        Example:
            .. code-block:: python

                # Transfer gift to another user
                app.transfer_gift(message_id=123, to_chat_id=123)

                # Pay up to 25 Stars if the transfer isn't free
                app.transfer_gift(message_id=123, to_chat_id=123, max_star_count=25)
        """
        peer = await self.resolve_peer(to_chat_id)

        if not isinstance(peer, (raw.types.InputPeerUser, raw.types.InputPeerSelf)):
            raise ValueError("chat_id must belong to a user.")

        try:
            await self.invoke(
                raw.functions.payments.TransferStarGift(
                    stargift=raw.types.InputSavedStarGiftUser(
                        msg_id=message_id
                    ),
                    to_id=peer
                )
            )
        except errors.PaymentRequired:
            # Stars are only spent when the caller agreed to, and never more than they allowed
            if max_star_count is None:
                raise

            invoice = raw.types.InputInvoiceStarGiftTransfer(
                stargift=raw.types.InputSavedStarGiftUser(
                    msg_id=message_id
                ),
                to_id=peer
            )

            await utils.pay_stars_invoice(self, invoice, max_star_count)

        return True
