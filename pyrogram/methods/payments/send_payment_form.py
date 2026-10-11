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

import re
from typing import Union, List

import pyrogram
from pyrogram import raw, types


class SendPaymentForm:
    async def send_payment_form(
        self: "pyrogram.Client", *,
        chat_id: Union[int, str] = None,
        message_id: int = None,
        invoice_link: str = None
    ) -> List[Union["types.Photo", "types.Video"]]:
        """Pay an invoice.

        .. note::

            For now only stars invoices are supported.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                of the target channel/supergroup (in the format @username).

            message_id (``int``):
                Pass a message identifier or to get the invoice from message.

            invoice_link (``str``):
                Pass a invoice link in form of a *t.me/$...* link or slug itself to pay this invoice.

        Returns:
            List of :obj:`~pyrogram.types.Photo` | :obj:`~pyrogram.types.Video`: On success, the list of bought photos and videos is returned.
            The list is empty when the invoice isn't for paid media.

        Example:
            .. code-block:: python

                # Pay invoice from message
                app.send_payment_form(chat_id=chat_id, message_id=123)

                # Pay invoice form from link
                app.send_payment_form(invoice_link="https://t.me/$xvbzUtt5sUlJCAAATqZrWRy9Yzk")
        """
        if not any((all((chat_id, message_id)), invoice_link)):
            raise ValueError("You should pass at least one parameter to this method.")

        form = None
        invoice = None

        if message_id:
            invoice = raw.types.InputInvoiceMessage(
                peer=await self.resolve_peer(chat_id),
                msg_id=message_id
            )
        elif invoice_link:
            match = re.match(r"^(?:https?://)?(?:www\.)?(?:t(?:elegram)?\.(?:org|me|dog)/\$)([\w-]+)$", invoice_link)

            if match:
                slug = match.group(1)
            else:
                slug = invoice_link

            invoice = raw.types.InputInvoiceSlug(
                slug=slug
            )

        form = await self.get_payment_form(chat_id=chat_id, message_id=message_id, invoice_link=invoice_link)

        r = await self.invoke(
            raw.functions.payments.SendStarsForm(
                form_id=form.id,
                invoice=invoice
            )
        )
        # TODO: Add support for regular invoices (credentials)

        # The stars are spent at this point: an error below would make a caller retry the "failed" call and pay again.
        # Every update is looked at, and anything that isn't a bought photo or video is skipped instead of raising.
        medias = []

        if isinstance(r, raw.types.payments.PaymentResult):
            updates = getattr(r.updates, "updates", None)

            if updates is None:
                updates = [getattr(r.updates, "update", None)]

            for update in updates:
                if not isinstance(update, raw.types.UpdateMessageExtendedMedia):
                    continue

                for ext_media in update.extended_media:
                    # Media that hasn't been bought (yet) is only a preview, without the media itself
                    media = getattr(ext_media, "media", None)

                    if isinstance(media, raw.types.MessageMediaPhoto):
                        if isinstance(media.photo, raw.types.Photo):
                            medias.append(types.Photo._parse(self, media.photo))
                    elif isinstance(media, raw.types.MessageMediaDocument):
                        doc = media.document

                        if not isinstance(doc, raw.types.Document):
                            continue

                        attributes = {type(i): i for i in doc.attributes}

                        file_name = getattr(
                            attributes.get(
                                raw.types.DocumentAttributeFilename, None
                            ), "file_name", None
                        )

                        video_attributes = attributes.get(raw.types.DocumentAttributeVideo)

                        if video_attributes is not None:
                            medias.append(types.Video._parse(self, doc, video_attributes, file_name))

            return types.List(medias)
