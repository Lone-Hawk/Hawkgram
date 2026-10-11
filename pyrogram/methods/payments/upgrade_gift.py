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

from typing import Optional

import pyrogram
from pyrogram import errors, raw, utils


class UpgradeGift:
    async def upgrade_gift(
        self: "pyrogram.Client",
        message_id: int,
        keep_details: Optional[bool] = None,
        max_star_count: Optional[int] = None
    ) -> bool:
        """Upgrade star gift to unique.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            message_id (``int``):
                Unique message identifier of star gift.

            keep_details (``bool``):
                Pass True if you want to keep the original details of the gift like caption.

            max_star_count (``int``, *optional*):
                The most Telegram Stars you agree to pay if the upgrade isn't free (wasn't paid for by the sender).
                By default nothing is paid: :obj:`~pyrogram.errors.PaymentRequired` is raised when the upgrade
                costs Stars. If it costs more than *max_star_count*, ``ValueError`` is raised and nothing is paid.

        Returns:
            ``bool``: On success, True is returned.

        Example:
            .. code-block:: python

                # Upgrade gift
                app.upgrade_gift(message_id=123)

                # Pay up to 50 Stars if the upgrade isn't free
                app.upgrade_gift(message_id=123, max_star_count=50)
        """
        try:
            await self.invoke(
                raw.functions.payments.UpgradeStarGift(
                    stargift=raw.types.InputSavedStarGiftUser(
                        msg_id=message_id
                    ),
                    keep_original_details=keep_details
                )
            )
        except errors.PaymentRequired:
            # Stars are only spent when the caller agreed to, and never more than they allowed
            if max_star_count is None:
                raise

            invoice = raw.types.InputInvoiceStarGiftUpgrade(
                stargift=raw.types.InputSavedStarGiftUser(
                    msg_id=message_id
                ),
                keep_original_details=keep_details
            )

            await utils.pay_stars_invoice(self, invoice, max_star_count)

        return True
