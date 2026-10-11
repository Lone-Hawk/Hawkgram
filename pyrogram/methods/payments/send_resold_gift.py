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


from typing import Optional, Union

import pyrogram
from pyrogram import raw, types, utils


class SendResoldGift:
    async def send_resold_gift(
        self: "pyrogram.Client",
        gift_link: str,
        new_owner_chat_id: Union[int, str],
        max_star_count: Optional[int] = None
    ) -> Optional["types.Message"]:
        """Send an upgraded gift that is available for resale to another user or channel chat.

        .. note::

            Gifts already owned by the current user must be transferred using :meth:`~pyrogram.Client.transfer_gift` and can't be passed to this method.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            gift_link (``str``):
                Link to the gift.

            new_owner_chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat you want to transfer the star gift to.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            max_star_count (``int``):
                The most Telegram Stars you agree to pay for the gift, usually its resale price when you chose it.
                The seller can change the price at any time: if it costs more, ``ValueError`` is raised and nothing is
                paid. Without it nothing is paid either, and the ``ValueError`` says the current price.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the sent message is returned.

        Example:
            .. code-block:: python

                # Transfer gift to another user
                await app.send_resold_gift(
                    gift_link="https://t.me/nft/NekoHelmet-9215", new_owner_chat_id=123, max_star_count=500
                )
        """
        match = self.UPGRADED_GIFT_RE.match(gift_link)

        if not match:
            raise ValueError(
                "Invalid gift link provided."
            )

        peer = await self.resolve_peer(new_owner_chat_id)

        invoice = raw.types.InputInvoiceStarGiftResale(
            slug=match.group(1),
            to_id=peer
        )

        # The resale price used to be paid whatever it was at that moment, even if the seller had just raised it
        r = await utils.pay_stars_invoice(self, invoice, max_star_count)

        # The result holds updates, not a list of messages: parse_messages() raised AttributeError here, after the
        # gift had been paid for
        return await utils.parse_message_from_updates(
            self, r.updates if isinstance(r, raw.types.payments.PaymentResult) else r
        )
