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

"""Regression tests for Client methods, with requests and answers going through FakeClient"""

from datetime import datetime

import pytest

from pyrogram import errors, raw, types, utils
from .test_layer_229 import FakeClient, USER_ID, CHANNEL_ID, CHANNEL_RAW_ID, raw_user, updates

T = raw.types

GROUP_RAW_ID = 77
OTHER_USER_ID = 3


@pytest.fixture
def client():
    return FakeClient()


def message(message_id, peer):
    return T.Message(id=message_id, peer_id=peer, date=1, message="text")


def found(*messages):
    return T.messages.Messages(messages=list(messages), topics=[], chats=[], users=[])


# ---------------------------------------------------------------------------------------------------------------
# delete_messages only deletes messages of the given chat
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("chat_id, own_peer", [
    (USER_ID, T.PeerUser(user_id=USER_ID)),
    (-GROUP_RAW_ID, T.PeerChat(chat_id=GROUP_RAW_ID)),
])
async def test_delete_messages_skips_messages_of_other_chats(client, chat_id, own_peer):
    # Private chats and basic groups share message ids: id 6 is in another chat, id 7 doesn't exist
    client.responses = [
        found(
            message(5, own_peer),
            message(6, T.PeerChat(chat_id=GROUP_RAW_ID + 1)),
            T.MessageEmpty(id=7),
            message(8, own_peer),
        ),
        T.messages.AffectedMessages(pts=10, pts_count=2),
    ]

    assert await client.delete_messages(chat_id, [5, 6, 7, 8], revoke=False) == 2

    get_messages, delete = client.requests
    assert get_messages.id == [T.InputMessageID(id=i) for i in (5, 6, 7, 8)]
    assert isinstance(delete, raw.functions.messages.DeleteMessages)
    assert delete.id == [5, 8]
    assert not delete.revoke


@pytest.mark.asyncio
async def test_delete_messages_deletes_nothing_when_no_message_is_in_the_chat(client):
    # A bot asked to delete message 6 "in chat USER_ID" must not delete it from another chat
    client.responses = [found(message(6, T.PeerUser(user_id=OTHER_USER_ID)))]

    assert await client.delete_messages(USER_ID, 6) == 0
    assert len(client.requests) == 1


@pytest.mark.asyncio
async def test_delete_messages_in_saved_messages(client):
    await client.storage.open()
    await client.storage.user_id(USER_ID)

    client.responses = [
        found(message(5, T.PeerUser(user_id=USER_ID)), message(6, T.PeerUser(user_id=OTHER_USER_ID))),
        T.messages.AffectedMessages(pts=10, pts_count=1),
    ]

    assert await client.delete_messages("me", [5, 6]) == 1
    assert client.requests[1].id == [5]


@pytest.mark.asyncio
async def test_delete_messages_in_channels_names_the_channel(client):
    client.responses = [T.messages.AffectedMessages(pts=10, pts_count=2)]

    assert await client.delete_messages(CHANNEL_ID, [5, 6]) == 2

    (delete,) = client.requests
    assert isinstance(delete, raw.functions.channels.DeleteMessages)
    assert delete.channel == T.InputPeerChannel(channel_id=CHANNEL_RAW_ID, access_hash=9)
    assert delete.id == [5, 6]


# ---------------------------------------------------------------------------------------------------------------
# send_payment_form only pays what the caller allows, and doesn't fail after the stars are spent
# ---------------------------------------------------------------------------------------------------------------

def raw_photo():
    return T.Photo(id=1, access_hash=2, file_reference=b"", date=1, dc_id=2,
                   sizes=[T.PhotoSize(type="x", w=10, h=10, size=100)])


def raw_document(*attributes):
    return T.Document(id=3, access_hash=4, file_reference=b"", date=1, mime_type="video/mp4", size=1000, dc_id=2,
                      attributes=list(attributes))


def extended_media(*medias, msg_id=1):
    return T.UpdateMessageExtendedMedia(peer=T.PeerUser(user_id=USER_ID), msg_id=msg_id, extended_media=list(medias))


def bought(media):
    return T.MessageExtendedMedia(media=media)


def stars_payment_form(star_count, currency="XTR"):
    return T.payments.PaymentFormStars(
        form_id=42, bot_id=USER_ID, title="Title", description="Description", users=[],
        invoice=T.Invoice(currency=currency, prices=[T.LabeledPrice(label="Media", amount=star_count)])
    )


async def pay(client, result):
    client.responses = [stars_payment_form(100), result]

    medias = await client.send_payment_form(invoice_link="https://t.me/$slug", max_star_count=100)

    # The form was paid exactly once
    get_form, request = client.requests
    assert isinstance(get_form.invoice, T.InputInvoiceSlug) and get_form.invoice.slug == "slug"
    assert isinstance(request, raw.functions.payments.SendStarsForm) and request.form_id == 42

    return medias


@pytest.mark.asyncio
async def test_send_payment_form_returns_every_bought_media(client):
    video = raw_document(T.DocumentAttributeVideo(duration=1, w=10, h=10), T.DocumentAttributeFilename(file_name="v.mp4"))
    result = T.payments.PaymentResult(updates=updates(
        T.UpdateConfig(),
        extended_media(bought(T.MessageMediaPhoto(photo=raw_photo())), msg_id=1),
        extended_media(bought(T.MessageMediaDocument(document=video)), msg_id=2),
    ))

    medias = await pay(client, result)

    # Only the first update with media used to be read
    assert [type(m) for m in medias] == [types.Photo, types.Video]
    assert medias[1].file_name == "v.mp4"


@pytest.mark.asyncio
@pytest.mark.parametrize("result", [
    # An invoice that isn't for paid media (used to return None)
    T.payments.PaymentResult(updates=updates(T.UpdateConfig())),
    # A single update (used to raise AttributeError)
    T.payments.PaymentResult(updates=T.UpdateShort(update=T.UpdateConfig(), date=1)),
    # Media still shown as a preview (used to raise AttributeError)
    T.payments.PaymentResult(updates=updates(extended_media(T.MessageExtendedMediaPreview(w=10, h=10)))),
    # A document that isn't a video (used to raise KeyError)
    T.payments.PaymentResult(updates=updates(extended_media(bought(T.MessageMediaDocument(
        document=raw_document(T.DocumentAttributeFilename(file_name="a.zip"))
    ))))),
], ids=["no-media", "update-short", "preview", "not-a-video"])
async def test_send_payment_form_does_not_fail_after_paying(client, result):
    medias = await pay(client, result)

    assert isinstance(medias, types.List) and list(medias) == []


@pytest.mark.asyncio
async def test_send_payment_form_pays_nothing_without_max_star_count(client):
    # Whatever the invoice cost used to be paid, e.g. for an invoice link a user had sent to a bot
    client.responses = [stars_payment_form(100)]

    with pytest.raises(ValueError, match="costs 100 Telegram Stars"):
        await client.send_payment_form(invoice_link="https://t.me/$slug")

    assert [type(r) for r in client.requests] == [raw.functions.payments.GetPaymentForm]


@pytest.mark.asyncio
@pytest.mark.parametrize("form", [stars_payment_form(101), stars_payment_form(100, currency="USD")],
                         ids=["too-much", "not-stars"])
async def test_send_payment_form_refuses_other_prices(client, form):
    client.responses = [form]

    with pytest.raises(ValueError, match="nothing was paid"):
        await client.send_payment_form(chat_id=USER_ID, message_id=7, max_star_count=100)

    (get_form,) = client.requests
    assert isinstance(get_form.invoice, T.InputInvoiceMessage) and get_form.invoice.msg_id == 7


# ---------------------------------------------------------------------------------------------------------------
# transfer_gift and upgrade_gift only pay what the caller allows
# ---------------------------------------------------------------------------------------------------------------

def gift_payment_form(star_count, currency="XTR"):
    return T.payments.PaymentFormStarGift(
        form_id=42,
        invoice=T.Invoice(currency=currency, prices=[T.LabeledPrice(label="Gift", amount=star_count)])
    )


async def transfer(client, **kwargs):
    return await client.transfer_gift(message_id=5, to_chat_id=USER_ID, **kwargs)


async def upgrade(client, **kwargs):
    return await client.upgrade_gift(message_id=5, **kwargs)


gift_actions = pytest.mark.parametrize("action, free_request, invoice_type", [
    (transfer, raw.functions.payments.TransferStarGift, T.InputInvoiceStarGiftTransfer),
    (upgrade, raw.functions.payments.UpgradeStarGift, T.InputInvoiceStarGiftUpgrade),
], ids=["transfer", "upgrade"])


@pytest.mark.asyncio
@gift_actions
async def test_free_gift_action_pays_nothing(client, action, free_request, invoice_type):
    client.responses = [updates()]

    assert await action(client) is True
    assert [type(r) for r in client.requests] == [free_request]


@pytest.mark.asyncio
@gift_actions
async def test_paid_gift_action_pays_nothing_by_default(client, action, free_request, invoice_type):
    # The stars used to be paid automatically, whatever the price
    client.responses = [errors.PaymentRequired()]

    with pytest.raises(errors.PaymentRequired):
        await action(client)

    assert [type(r) for r in client.requests] == [free_request]


@pytest.mark.asyncio
@gift_actions
async def test_paid_gift_action_pays_within_max_star_count(client, action, free_request, invoice_type):
    client.responses = [errors.PaymentRequired(), gift_payment_form(25), T.payments.PaymentResult(updates=updates())]

    assert await action(client, max_star_count=25) is True

    _, get_form, pay = client.requests
    assert isinstance(get_form, raw.functions.payments.GetPaymentForm)
    assert isinstance(get_form.invoice, invoice_type)
    assert isinstance(pay, raw.functions.payments.SendStarsForm)
    assert pay.form_id == 42 and pay.invoice == get_form.invoice


@pytest.mark.asyncio
@gift_actions
@pytest.mark.parametrize("form", [gift_payment_form(26), gift_payment_form(25, currency="USD")], ids=["too-much", "not-stars"])
async def test_paid_gift_action_refuses_other_prices(client, action, free_request, invoice_type, form):
    client.responses = [errors.PaymentRequired(), form]

    with pytest.raises(ValueError, match="nothing was paid"):
        await action(client, max_star_count=25)

    assert not any(isinstance(r, raw.functions.payments.SendStarsForm) for r in client.requests)


@pytest.mark.asyncio
async def test_gift_shortcuts_pass_max_star_count(client):
    gift = types.Gift(client=client, id=1, message_id=5)

    for call in (gift.transfer(USER_ID), gift.upgrade()):
        client.responses = [errors.PaymentRequired()]

        with pytest.raises(errors.PaymentRequired):
            await call

    client.requests.clear()
    client.responses = [errors.PaymentRequired(), gift_payment_form(10), T.payments.PaymentResult(updates=updates())]

    assert await gift.transfer(USER_ID, max_star_count=10) is True
    assert isinstance(client.requests[-1], raw.functions.payments.SendStarsForm)


# ---------------------------------------------------------------------------------------------------------------
# send_gift only pays the price the caller agreed to
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_gift_pays_nothing_without_max_star_count(client):
    # The gift's price used to be paid whatever it was, e.g. for a gift_id that came from user input
    client.responses = [gift_payment_form(999999)]

    with pytest.raises(ValueError, match="costs 999999 Telegram Stars"):
        await client.send_gift(chat_id=USER_ID, gift_id=1)

    assert [type(r) for r in client.requests] == [raw.functions.payments.GetPaymentForm]


@pytest.mark.asyncio
@pytest.mark.parametrize("form", [gift_payment_form(51), gift_payment_form(50, currency="USD")],
                         ids=["too-much", "not-stars"])
async def test_send_gift_refuses_other_prices(client, form):
    client.responses = [form]

    with pytest.raises(ValueError, match="nothing was paid"):
        await client.send_gift(chat_id=USER_ID, gift_id=1, max_star_count=50)

    assert not any(isinstance(r, raw.functions.payments.SendStarsForm) for r in client.requests)


@pytest.mark.asyncio
async def test_send_gift_pays_within_max_star_count(client):
    client.responses = [gift_payment_form(50), T.payments.PaymentResult(updates=updates())]

    assert await client.send_gift(chat_id=USER_ID, gift_id=1, text="Hi", pay_for_upgrade=True, max_star_count=50) is True

    get_form, pay = client.requests
    assert isinstance(get_form.invoice, T.InputInvoiceStarGift)
    assert get_form.invoice.gift_id == 1 and get_form.invoice.include_upgrade
    assert get_form.invoice.message.text == "Hi"
    assert isinstance(pay, raw.functions.payments.SendStarsForm)
    assert pay.form_id == 42 and pay.invoice == get_form.invoice


# ---------------------------------------------------------------------------------------------------------------
# Short message updates followed by a difference without messages
# ---------------------------------------------------------------------------------------------------------------

def short_message():
    return T.UpdateShortMessage(id=5, user_id=USER_ID, message="hi", pts=11, pts_count=1, date=1)


@pytest.mark.asyncio
@pytest.mark.parametrize("difference", [
    T.updates.DifferenceEmpty(date=1, seq=0),
    T.updates.DifferenceTooLong(pts=20),
], ids=["empty", "too-long"])
async def test_short_message_with_an_empty_difference_is_ignored(client, difference):
    await client.storage.open()
    client.responses = [difference]

    # This used to raise AttributeError (no new_messages), losing the update handling task
    await client.handle_updates(short_message())

    assert isinstance(client.requests[0], raw.functions.updates.GetDifference)
    assert client.dispatcher.updates_queue.empty()


@pytest.mark.asyncio
async def test_short_message_is_dispatched_from_the_difference(client):
    await client.storage.open()
    client.responses = [T.updates.Difference(
        new_messages=[message(5, T.PeerUser(user_id=USER_ID))], new_encrypted_messages=[], other_updates=[],
        chats=[], users=[], state=T.updates.State(pts=11, qts=0, date=1, seq=0, unread_count=0)
    )]

    await client.handle_updates(short_message())

    update, users, chats = client.dispatcher.updates_queue.get_nowait()
    assert isinstance(update, T.UpdateNewMessage) and update.message.id == 5


# ---------------------------------------------------------------------------------------------------------------
# leave_chat drops the channel's update state, by its id, once it has been left
# ---------------------------------------------------------------------------------------------------------------

async def client_with_channel_state(client):
    await client.storage.open()
    await client.storage.update_state((CHANNEL_ID, 5, None, 1, None))
    await client.storage.update_state((0, 9, None, 1, None))

    async def resolve_peer(peer_id):
        return T.InputPeerChannel(channel_id=CHANNEL_RAW_ID, access_hash=9)

    client.resolve_peer = resolve_peer

    return client


async def state_ids(client):
    return sorted(state[0] for state in await client.storage.update_state())


@pytest.mark.asyncio
@pytest.mark.parametrize("chat_id", [CHANNEL_ID, "@channel", "https://t.me/channel"])
async def test_leave_chat_removes_the_channel_state(client, chat_id):
    # The state was looked up by chat_id as given, and only with skip_updates=False (the default is True)
    client = await client_with_channel_state(client)
    client.responses = [updates()]

    await client.leave_chat(chat_id)

    assert isinstance(client.requests[0], raw.functions.channels.LeaveChannel)
    assert await state_ids(client) == [0]


@pytest.mark.asyncio
async def test_leave_chat_keeps_the_state_when_leaving_fails(client):
    client = await client_with_channel_state(client)
    client.skip_updates = False
    client.responses = [errors.ChannelPrivate()]

    with pytest.raises(errors.ChannelPrivate):
        await client.leave_chat(CHANNEL_ID)

    assert await state_ids(client) == [CHANNEL_ID, 0]


# ---------------------------------------------------------------------------------------------------------------
# delete_chat_history in channels
# ---------------------------------------------------------------------------------------------------------------

def deleted_in_channel(*message_ids):
    return T.UpdateDeleteChannelMessages(channel_id=CHANNEL_RAW_ID, messages=list(message_ids), pts=1, pts_count=1)


@pytest.mark.asyncio
@pytest.mark.parametrize("response, expected", [
    (updates(), 0),  # used to raise IndexError, after the history had been deleted
    (updates(T.UpdateConfig(), deleted_in_channel(1, 2), deleted_in_channel(3)), 3),
], ids=["no-updates", "several-updates"])
async def test_delete_chat_history_in_channels_counts_deleted_messages(client, response, expected):
    client.responses = [response]

    assert await client.delete_chat_history(CHANNEL_ID, revoke=True) == expected
    assert isinstance(client.requests[0], raw.functions.channels.DeleteHistory)


@pytest.mark.asyncio
@pytest.mark.parametrize("kwargs", [
    {"min_date": datetime(2026, 1, 1)},
    {"max_date": datetime(2026, 1, 1)},
    {"just_clear": True},
], ids=["min_date", "max_date", "just_clear"])
async def test_delete_chat_history_in_channels_refuses_unsupported_options(client, kwargs):
    # These were ignored for channels, so asking to delete a date range deleted the whole history
    with pytest.raises(ValueError):
        await client.delete_chat_history(CHANNEL_ID, revoke=True, **kwargs)

    assert client.requests == []


@pytest.mark.asyncio
async def test_delete_chat_history_by_date_in_private_chats(client):
    client.responses = [T.messages.AffectedHistory(pts=10, pts_count=4, offset=0)]

    assert await client.delete_chat_history(USER_ID, min_date=datetime(2026, 1, 1)) == 4
    assert client.requests[0].min_date == utils.datetime_to_timestamp(datetime(2026, 1, 1))


# ---------------------------------------------------------------------------------------------------------------
# send_resold_gift only pays the price the caller agreed to
# ---------------------------------------------------------------------------------------------------------------

GIFT_LINK = "https://t.me/nft/NekoHelmet-9215"


@pytest.mark.asyncio
async def test_resold_gift_is_not_bought_without_max_star_count(client):
    # The current resale price used to be paid, whatever the seller had just set it to
    client.responses = [gift_payment_form(500)]

    with pytest.raises(ValueError, match="costs 500 Telegram Stars"):
        await client.send_resold_gift(GIFT_LINK, USER_ID)

    (get_form,) = client.requests
    assert isinstance(get_form.invoice, T.InputInvoiceStarGiftResale) and get_form.invoice.slug == "NekoHelmet-9215"


@pytest.mark.asyncio
async def test_resold_gift_is_not_bought_above_max_star_count(client):
    client.responses = [gift_payment_form(501)]

    with pytest.raises(ValueError, match="nothing was paid"):
        await client.send_resold_gift(GIFT_LINK, USER_ID, max_star_count=500)

    assert not any(isinstance(r, raw.functions.payments.SendStarsForm) for r in client.requests)


@pytest.mark.asyncio
async def test_resold_gift_is_bought_within_max_star_count(client):
    client.responses = [gift_payment_form(500), T.payments.PaymentResult(updates=updates())]

    assert await client.send_resold_gift(GIFT_LINK, USER_ID, max_star_count=500) is None

    get_form, pay = client.requests
    assert isinstance(pay, raw.functions.payments.SendStarsForm)
    assert pay.form_id == 42 and pay.invoice == get_form.invoice


@pytest.mark.asyncio
async def test_resold_gift_returns_the_gift_message(client):
    # Parsing the payment result used to raise AttributeError, after the gift had been paid for
    gift_message = message(9, T.PeerUser(user_id=USER_ID))
    client.responses = [
        gift_payment_form(500),
        T.payments.PaymentResult(updates=updates(
            T.UpdateNewMessage(message=gift_message, pts=1, pts_count=1), users=[raw_user()]
        )),
    ]

    sent = await client.send_resold_gift(GIFT_LINK, USER_ID, max_star_count=500)

    assert isinstance(sent, types.Message) and sent.id == 9
