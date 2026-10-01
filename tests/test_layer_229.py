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

"""Offline tests for the high-level wrappers of Telegram API layer 229.

Requests are captured by a fake ``invoke`` that also serializes and deserializes every request, so each raw
request built by a wrapper is checked to be valid on the wire. Responses are canned raw objects.
"""

from io import BytesIO

import pytest

import pyrogram
from pyrogram import enums, raw, types, utils
from pyrogram.dispatcher import Dispatcher
from pyrogram.raw.core import TLObject

T = raw.types

USER_ID = 1001
BOT_ID = 2002
CHANNEL_RAW_ID = 3003
CHANNEL_ID = utils.get_channel_id(CHANNEL_RAW_ID)
COMMUNITY_RAW_ID = 4004
COMMUNITY_ID = utils.get_channel_id(COMMUNITY_RAW_ID)


def wire(obj):
    """Round-trip a raw object through serialization, so it looks exactly like data received from Telegram
    (e.g. absent optional vectors become empty lists instead of None)."""
    return TLObject.read(BytesIO(obj.write()))


def text(value):
    return T.TextWithEntities(text=value, entities=[])


def raw_user(user_id=USER_ID, bot=False):
    return wire(T.User(id=user_id, access_hash=7, first_name=f"user{user_id}", bot=bot or None))


def raw_channel(channel_id=CHANNEL_RAW_ID, **kwargs):
    return wire(T.Channel(id=channel_id, access_hash=9, title="Channel", photo=T.ChatPhotoEmpty(), date=1,
                          megagroup=True, **kwargs))


def raw_community(community_id=COMMUNITY_RAW_ID):
    return wire(T.Community(id=community_id, access_hash=11, title="Community", photo=T.ChatPhotoEmpty(), date=1,
                            creator=True))


class FakeClient(pyrogram.Client):
    """A Client that never connects: invoke() records requests and returns queued responses."""

    def __init__(self):
        super().__init__("test", api_id=1, api_hash="0" * 32, in_memory=True, no_updates=True)
        self.requests = []
        self.responses = []

    async def invoke(self, query, *args, **kwargs):
        # Every request must survive a serialization round trip, which validates flags and field types
        TLObject.read(BytesIO(query.write()))
        self.requests.append(query)
        response = self.responses.pop(0) if self.responses else True
        return wire(response) if isinstance(response, TLObject) else response

    async def resolve_peer(self, peer_id):
        if peer_id in ("me", "self"):
            return T.InputPeerSelf()
        if isinstance(peer_id, str):
            return T.InputPeerUser(user_id=BOT_ID, access_hash=8)
        if peer_id > 0:
            return T.InputPeerUser(user_id=peer_id, access_hash=7)
        if str(peer_id).startswith("-100"):
            return T.InputPeerChannel(channel_id=utils.get_channel_id(peer_id), access_hash=9)
        return T.InputPeerChat(chat_id=-peer_id)


@pytest.fixture
def client():
    return FakeClient()


def updates(*items, users=(), chats=()):
    return T.Updates(updates=list(items), users=list(users), chats=list(chats), date=1, seq=0)


def ephemeral(message_id=5, out=True, **kwargs):
    return wire(T.EphemeralMessage(
        id=message_id, from_id=T.PeerUser(user_id=BOT_ID), peer_id=T.PeerChannel(channel_id=CHANNEL_RAW_ID),
        receiver_id=USER_ID, date=1, message="secret", out=out or None, **kwargs
    ))


# ---------------------------------------------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------------------------------------------

def test_rich_message_text_and_write():
    photo = T.Photo(id=10, access_hash=11, file_reference=b"ref", date=1,
                    sizes=[T.PhotoSize(type="x", w=10, h=10, size=100)], dc_id=2)
    rich = T.RichMessage(
        blocks=[
            T.PageBlockHeading1(text=T.TextPlain(text="Title")),
            T.PageBlockParagraph(text=T.TextConcat(texts=[T.TextBold(text=T.TextPlain(text="Bold")),
                                                          T.TextPlain(text=" plain")])),
            T.PageBlockList(items=[T.PageListItemText(text=T.TextPlain(text="one")),
                                   T.PageListItemText(text=T.TextPlain(text="two"))]),
            T.PageBlockMath(source="e=mc^2"),
            T.PageBlockParagraph(text=T.TextCustomEmoji(document_id=1, alt="🔥")),
            T.PageBlockPhoto(photo_id=10, caption=T.PageCaption(text=T.TextPlain(text="A photo"),
                                                                credit=T.TextEmpty())),
        ],
        photos=[photo], documents=[], part=True,
    )

    rich = wire(rich)
    parsed = types.RichMessage._parse(None, rich)

    assert parsed.text == "Title\nBold plain\none\ntwo\ne=mc^2\n🔥\nA photo"
    assert parsed.is_partial is True
    assert len(parsed.photos) == 1

    written = parsed.write()
    assert isinstance(written, T.InputRichMessage)
    assert written.blocks == rich.blocks
    assert written.photos[0].id == 10 and written.photos[0].file_reference == b"ref"


def test_rich_message_build_input():
    html = types.RichMessage._build_input(html="<b>x</b>", is_rtl=True, disable_auto_links=True)
    assert isinstance(html, T.InputRichMessageHTML) and html.rtl and html.noautolink

    markdown = types.RichMessage._build_input(markdown="# x")
    assert isinstance(markdown, T.InputRichMessageMarkdown) and markdown.rtl is None

    with pytest.raises(ValueError):
        types.RichMessage._build_input(html="a", markdown="b")

    with pytest.raises(ValueError):
        types.RichMessage._build_input()


def test_ai_compose_tone_parse_and_input():
    default = types.AiComposeTone._parse(None, T.AiComposeToneDefault(tone="formal", emoji_id=1, title="Formal"))
    assert default.is_default and default.name == "formal"
    assert isinstance(default.write(), T.InputAiComposeToneDefault)

    custom = types.AiComposeTone._parse(
        None,
        wire(T.AiComposeTone(id=5, access_hash=6, slug="pirate", title="Pirate", author_id=USER_ID, installs_count=3,
                        example_english=T.AiComposeToneExample(from_peer=text("hello"), to=text("ahoy")))),
        {USER_ID: raw_user()},
    )
    assert custom.install_count == 3 and custom.author.id == USER_ID
    assert custom.example.text == "hello" and custom.example.result_text == "ahoy"
    assert isinstance(custom.write(), T.InputAiComposeToneID)

    assert isinstance(types.AiComposeTone._to_input("pirate"), T.InputAiComposeToneSlug)
    single_use = T.InputAiComposeToneSingleUse(custom_prompt="x")
    assert types.AiComposeTone._to_input(single_use) is single_use
    assert types.AiComposeTone._to_input(None) is None

    with pytest.raises(TypeError):
        types.AiComposeTone._to_input(123)


def test_diff_entities_parse_and_write():
    composed = types.ComposedText._parse(None, wire(T.messages.ComposedMessageWithAI(
        result_text=text("I have an apple"),
        diff_text=T.TextWithEntities(text="I has have a an apple", entities=[
            T.MessageEntityDiffDelete(offset=2, length=3),
            T.MessageEntityDiffReplace(offset=10, length=2, old_text="a"),
        ]),
    )))

    assert composed.text == "I have an apple"
    delete, replace = composed.diff_entities
    assert delete.type == enums.MessageEntityType.DIFF_DELETE
    assert replace.type == enums.MessageEntityType.DIFF_REPLACE and replace.old_text == "a"


@pytest.mark.asyncio
async def test_diff_replace_entity_write_keeps_old_text():
    replace = types.MessageEntity._parse(None, T.MessageEntityDiffReplace(offset=0, length=1, old_text="a"), {})
    bold = types.MessageEntity._parse(None, T.MessageEntityBold(offset=0, length=1), {})

    assert (await replace.write()).old_text == "a"
    assert isinstance(await bold.write(), T.MessageEntityBold)


@pytest.mark.asyncio
async def test_formatted_date_entity_parse_and_write():
    raw_entity = wire(T.MessageEntityFormattedDate(offset=3, length=8, date=1700000000, short_date=True, relative=True))
    entity = types.MessageEntity._parse(None, raw_entity, {})

    assert entity.type == enums.MessageEntityType.FORMATTED_DATE
    assert entity.date == utils.timestamp_to_datetime(1700000000)
    assert wire(await entity.write()) == raw_entity


@pytest.mark.asyncio
async def test_unknown_entity_type_falls_back_to_unknown():
    class FutureEntity:
        """An entity type from a layer newer than this library, carrying a field MessageEntityUnknown lacks."""
        offset, length, url = 2, 4, "https://example.com"

    entity = types.MessageEntity._parse(None, FutureEntity(), {})

    assert entity.type == enums.MessageEntityType.UNKNOWN
    assert await entity.write() == T.MessageEntityUnknown(offset=2, length=4)


@pytest.mark.asyncio
async def test_message_with_formatted_date_is_parsed(client):
    message = await types.Message._parse(client, wire(T.Message(
        id=1, peer_id=T.PeerChannel(channel_id=CHANNEL_RAW_ID), date=1, message="Meet at noon",
        entities=[T.MessageEntityFormattedDate(offset=8, length=4, date=1700000000, short_time=True)],
    )), {}, {CHANNEL_RAW_ID: raw_channel()})

    assert message.text == "Meet at noon"
    assert message.entities[0].type == enums.MessageEntityType.FORMATTED_DATE


@pytest.mark.asyncio
async def test_poll_new_fields_and_added_options():
    poll = T.Poll(id=1, question=text("Lunch?"), hash=0, open_answers=True, revoting_disabled=True,
                  shuffle_answers=True, subscribers_only=True, countries_iso2=["LK"], answers=[
                      T.PollAnswer(text=text("Rice"), option=b"\x00"),
                      T.PollAnswer(text=text("Pizza"), option=b"\x01", added_by=T.PeerUser(user_id=USER_ID),
                                   date=1700000000),
                  ])
    results = T.PollResults(has_unread_votes=True, results=[
        T.PollAnswerVoters(option=b"\x00", voters=2, recent_voters=[], chosen=True),
        T.PollAnswerVoters(option=b"\x01"),
    ], total_voters=2, recent_voters=[])

    parsed = await types.Poll._parse(None, wire(T.MessageMediaPoll(poll=poll, results=results)), {USER_ID: raw_user()})

    assert parsed.allows_adding_options and parsed.shuffle_options and parsed.members_only
    assert parsed.allows_revoting is False
    assert parsed.country_codes == ["LK"] and parsed.has_unread_votes
    assert [o.voter_count for o in parsed.options] == [2, 0]
    assert parsed.options[1].added_by.id == USER_ID and parsed.options[1].added_date is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("action, service, attribute, expected", [
    (T.MessageActionChatJoinedViaCommunity(community_id=COMMUNITY_RAW_ID),
     enums.MessageServiceType.CHAT_JOINED_FROM_COMMUNITY, "chat_joined_from_community_id", COMMUNITY_ID),
    (T.MessageActionChangeCommunity(community_id=COMMUNITY_RAW_ID),
     enums.MessageServiceType.CHAT_ADDED_TO_COMMUNITY, "chat_added_to_community_id", COMMUNITY_ID),
    (T.MessageActionChangeCommunity(),
     enums.MessageServiceType.CHAT_REMOVED_FROM_COMMUNITY, "chat_removed_from_community", True),
])
async def test_community_service_messages(client, action, service, attribute, expected):
    message = wire(T.MessageService(id=1, peer_id=T.PeerChannel(channel_id=CHANNEL_RAW_ID), date=1, action=action))
    parsed = await types.Message._parse(client, message, {}, {CHANNEL_RAW_ID: raw_channel()})

    assert parsed.service == service
    assert getattr(parsed, attribute) == expected


@pytest.mark.asyncio
async def test_other_new_service_messages(client):
    chats = {CHANNEL_RAW_ID: raw_channel()}
    peer = T.PeerChannel(channel_id=CHANNEL_RAW_ID)

    managed = await types.Message._parse(client, wire(T.MessageService(
        id=1, peer_id=peer, date=1, action=T.MessageActionManagedBotCreated(bot_id=BOT_ID)
    )), {BOT_ID: raw_user(BOT_ID, bot=True)}, chats)
    assert managed.service == enums.MessageServiceType.MANAGED_BOT_CREATED
    assert managed.managed_bot_created.bot.id == BOT_ID

    added = await types.Message._parse(client, wire(T.MessageService(
        id=2, peer_id=peer, date=1,
        action=T.MessageActionPollAppendAnswer(answer=T.PollAnswer(text=text("Tea"), option=b"\x02"))
    )), {}, chats)
    assert added.service == enums.MessageServiceType.POLL_OPTION_ADDED
    assert added.poll_option_added.text == "Tea" and added.poll_option_added.data == b"\x02"


# ---------------------------------------------------------------------------------------------------------------
# Communities in Chat, peer caching and full info
# ---------------------------------------------------------------------------------------------------------------

def test_community_chat_parsing():
    chat = types.Chat._parse_chat(None, raw_community())
    assert chat.type == enums.ChatType.COMMUNITY and chat.id == COMMUNITY_ID and chat.is_creator

    forbidden = types.Chat._parse_chat(None, wire(T.CommunityForbidden(id=COMMUNITY_RAW_ID, title="Gone")))
    assert forbidden.type == enums.ChatType.COMMUNITY and forbidden.title == "Gone"

    member = types.Chat._parse_chat(None, raw_channel(linked_community_id=COMMUNITY_RAW_ID))
    assert member.community_id == COMMUNITY_ID


@pytest.mark.asyncio
async def test_community_full_info():
    full = wire(T.messages.ChatFull(
        full_chat=T.CommunityFull(id=COMMUNITY_RAW_ID, about="All my projects", chat_photo=T.PhotoEmpty(id=0),
                                  peer_link_requests_pending=2,
                                  linked_peers=[T.CommunityPeer(peer=T.PeerChannel(channel_id=CHANNEL_RAW_ID)),
                                                T.CommunityPeer(peer=T.PeerUser(user_id=BOT_ID))]),
        chats=[raw_community(), raw_channel()], users=[raw_user(BOT_ID, bot=True)],
    ))

    chat = await types.Chat._parse_full(None, full)

    assert chat.type == enums.ChatType.COMMUNITY and chat.description == "All my projects"
    assert chat.community_link_requests_count == 2
    assert [c.id for c in chat.community_chats] == [CHANNEL_ID, BOT_ID]


@pytest.mark.asyncio
async def test_fetch_peers_caches_communities(client):
    stored = []

    class Storage:
        async def update_peers(self, peers):
            stored.extend(peers)

        async def update_usernames(self, usernames):
            pass

    client.storage = Storage()
    await client.fetch_peers([raw_community(), T.CommunityForbidden(id=5, title="no hash")])

    assert stored == [(COMMUNITY_ID, 11, "channel", None, None)]


# ---------------------------------------------------------------------------------------------------------------
# Methods
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_community(client):
    client.responses = [updates(chats=[raw_channel(), raw_community()])]

    community = await client.create_community("Projects", CHANNEL_ID, description="desc", is_chat_hidden=True)

    request = client.requests[0]
    assert isinstance(request, raw.functions.communities.Create)
    assert request.hidden and request.about == "desc" and isinstance(request.peer, T.InputPeerChannel)
    assert community.type == enums.ChatType.COMMUNITY and community.id == COMMUNITY_ID


@pytest.mark.asyncio
async def test_community_management_requests(client):
    await client.approve_community_link_request(COMMUNITY_ID, CHANNEL_ID)
    await client.decline_community_link_request(COMMUNITY_ID, CHANNEL_ID)
    await client.ban_community_member(COMMUNITY_ID, USER_ID)
    await client.unban_community_member(COMMUNITY_ID, USER_ID)
    await client.set_community_chat_hidden(COMMUNITY_ID, CHANNEL_ID, is_hidden=False)
    await client.remove_chat_from_community(COMMUNITY_ID, CHANNEL_ID)
    await client.set_community_collapsed(COMMUNITY_ID)

    approve, decline, ban, unban, show, remove, collapse = client.requests
    for request in client.requests:
        assert request.community == T.InputChannel(channel_id=COMMUNITY_RAW_ID, access_hash=9)
    assert not approve.reject and decline.reject
    assert not ban.unban and unban.unban
    assert show.visible and not show.hidden and not show.deleted
    assert remove.deleted
    assert collapse.collapsed


@pytest.mark.asyncio
async def test_get_community_link_requests_paginates(client):
    def page(peer_id, next_offset):
        return T.communities.PeerLinkRequests(
            total_count=2, next_offset=next_offset, chats=[raw_channel(peer_id)], users=[raw_user()],
            requests=[T.CommunityPeerRequest(peer=T.PeerChannel(channel_id=peer_id), requested_by=USER_ID, date=1)],
        )

    client.responses = [page(10, "next"), page(11, None)]

    requests = [r async for r in client.get_community_link_requests(COMMUNITY_ID)]

    assert [r.chat.id for r in requests] == [utils.get_channel_id(10), utils.get_channel_id(11)]
    assert requests[0].requested_by.id == USER_ID and requests[0].community_id == COMMUNITY_ID
    assert client.requests[1].offset == "next"


@pytest.mark.asyncio
async def test_send_ephemeral_message(client):
    client.responses = [updates(T.UpdateNewEphemeralMessage(message=ephemeral()),
                                users=[raw_user(), raw_user(BOT_ID, bot=True)], chats=[raw_channel()])]

    message = await client.send_ephemeral_message(CHANNEL_ID, USER_ID, "secret", reply_to_ephemeral_message_id=3,
                                                  callback_query_id="42", protect_content=True)

    request = client.requests[0]
    assert isinstance(request, raw.functions.ephemeral.SendMessage)
    assert request.receiver_id == T.InputUser(user_id=USER_ID, access_hash=7)
    assert request.reply_to == T.InputReplyToEphemeralMessage(id=3)
    assert request.query_id == 42 and request.noforwards

    assert isinstance(message, types.EphemeralMessage)
    assert message.text == "secret" and message.receiver_user_id == USER_ID and message.chat.id == CHANNEL_ID


@pytest.mark.asyncio
async def test_ephemeral_message_is_not_cached(client):
    regular = await types.Message._parse(client, wire(T.Message(id=5, peer_id=T.PeerChannel(channel_id=CHANNEL_RAW_ID),
                                                           date=1, message="regular")), {}, {CHANNEL_RAW_ID: raw_channel()})
    await types.EphemeralMessage._parse_ephemeral(client, ephemeral(message_id=5), {}, {CHANNEL_RAW_ID: raw_channel()})

    assert client.message_cache[(CHANNEL_ID, 5)] is regular


@pytest.mark.asyncio
async def test_welcome_messages(client):
    client.responses = [updates(T.UpdateNewEphemeralMessage(message=ephemeral(welcome_template=True)),
                                chats=[raw_channel()])]
    added = await client.add_welcome_message(CHANNEL_ID, "Welcome!")

    request = client.requests[0]
    assert request.welcome and isinstance(request.receiver_id, T.InputUserEmpty)
    assert added.is_welcome_template

    # The list of welcome messages doesn't include the chat, so it's fetched separately
    client.responses = [T.ephemeral.WelcomeMessages(hash=0, messages=[ephemeral()]),
                        T.messages.Chats(chats=[raw_channel()])]
    welcome = await client.get_welcome_messages(CHANNEL_ID)

    assert len(welcome) == 1 and welcome[0].chat.id == CHANNEL_ID
    assert any(isinstance(r, raw.functions.channels.GetChannels) for r in client.requests)


@pytest.mark.asyncio
async def test_ephemeral_bound_reply_goes_to_other_side(client):
    received = await types.EphemeralMessage._parse_ephemeral(
        client, ephemeral(out=False), {BOT_ID: raw_user(BOT_ID, bot=True)}, {CHANNEL_RAW_ID: raw_channel()}
    )
    client.responses = [updates()]

    await received.reply("pong")

    request = client.requests[0]
    assert request.receiver_id.user_id == BOT_ID
    assert request.reply_to == T.InputReplyToEphemeralMessage(id=5)


@pytest.mark.asyncio
async def test_compose_text_with_ai(client):
    client.responses = [T.messages.ComposedMessageWithAI(result_text=text("Ahoy"))]

    result = await client.compose_text_with_ai("Hello", custom_prompt="like a pirate", add_emojis=True)

    request = client.requests[0]
    assert request.tone == T.InputAiComposeToneSingleUse(custom_prompt="like a pirate") and request.emojify
    assert result.text == "Ahoy"

    with pytest.raises(ValueError):
        await client.compose_text_with_ai("Hello", tone="pirate", custom_prompt="x")


@pytest.mark.asyncio
async def test_translate_message_text_tone(client):
    client.responses = [T.messages.TranslateResult(result=[text("Hallo")])]

    await client.translate_message_text("de", text="Hello", tone="formal")

    assert client.requests[0].tone == "formal"


@pytest.mark.asyncio
async def test_send_rich_message(client):
    rich = T.RichMessage(blocks=[T.PageBlockHeading1(text=T.TextPlain(text="Notes"))], photos=[], documents=[])
    client.responses = [updates(T.UpdateNewChannelMessage(
        message=T.Message(id=9, peer_id=T.PeerChannel(channel_id=CHANNEL_RAW_ID), date=1, message="", rich_message=rich),
        pts=1, pts_count=1,
    ), chats=[raw_channel()])]

    message = await client.send_rich_message(CHANNEL_ID, markdown="# Notes")

    request = client.requests[0]
    assert request.message == "" and request.rich_message == T.InputRichMessageMarkdown(markdown="# Notes")
    assert message.rich_message.text == "Notes"


@pytest.mark.asyncio
async def test_send_poll_new_options(client):
    client.responses = [updates()]

    await client.send_poll(CHANNEL_ID, "Lunch?", [types.PollOption("Rice"), types.PollOption("Pizza")], allows_revoting=False, shuffle_options=True,
                           allows_adding_options=True, members_only=True, country_codes=["LK"])

    poll = client.requests[0].media.poll
    assert poll.revoting_disabled and poll.shuffle_answers and poll.open_answers and poll.subscribers_only
    assert poll.countries_iso2 == ["LK"] and poll.hash == 0


@pytest.mark.asyncio
async def test_add_and_delete_poll_option(client):
    await client.add_poll_option(CHANNEL_ID, 1, "Tea")
    assert isinstance(client.requests[0].answer, T.InputPollAnswer)

    async def get_messages(chat_id, message_ids):
        return types.Message(id=1, poll=types.Poll(id="1", question="?", total_voter_count=0, is_closed=False,
                                                   options=[types.PollOption(text="a", data=b"\x00"),
                                                            types.PollOption(text="b", data=b"\x01")]))

    client.get_messages = get_messages
    await client.delete_poll_option(CHANNEL_ID, 1, 1)
    assert client.requests[1].option == b"\x01"


@pytest.mark.asyncio
async def test_answer_chat_join_query(client):
    await client.answer_chat_join_query(1, enums.ChatJoinQueryResult.DECLINED)
    await client.answer_chat_join_query(2, web_app_url="https://example.com")

    assert isinstance(client.requests[0].result, T.JoinChatBotResultDeclined)
    assert client.requests[1].result == T.JoinChatBotResultWebView(url="https://example.com")

    with pytest.raises(ValueError):
        await client.answer_chat_join_query(3)


@pytest.mark.asyncio
async def test_set_chat_join_requests_with_guard_bot(client):
    await client.set_chat_join_requests(CHANNEL_ID, True, guard_bot_id="guard_bot", apply_to_invite_links=True)

    request = client.requests[0]
    assert request.channel == T.InputChannel(channel_id=CHANNEL_RAW_ID, access_hash=9)
    assert request.guard_bot == T.InputUser(user_id=BOT_ID, access_hash=8) and request.apply_to_invites


@pytest.mark.asyncio
async def test_web_browser_settings(client):
    client.responses = [T.account.WebBrowserSettings(
        open_external_browser=True, hash=0, inapp_exceptions=[],
        external_exceptions=[T.WebDomainException(domain="example.com", url="https://example.com", title="Example")],
    )]

    settings = await client.get_web_browser_settings()

    assert settings.open_external_browser and not settings.show_close_button
    assert settings.external_exceptions[0].domain == "example.com"


@pytest.mark.asyncio
async def test_managed_bot_access_settings(client):
    client.responses = [True, T.bots.AccessSettings(restricted=True, add_users=[raw_user()])]

    await client.set_managed_bot_access_settings(BOT_ID, True, [USER_ID])
    settings = await client.get_managed_bot_access_settings(BOT_ID)

    assert client.requests[0].add_users == [T.InputUser(user_id=USER_ID, access_hash=7)]
    assert settings.is_restricted and settings.allowed_users[0].id == USER_ID


# ---------------------------------------------------------------------------------------------------------------
# Updates
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_parses_new_updates(client):
    dispatcher = Dispatcher(client)
    users = {USER_ID: raw_user(), BOT_ID: raw_user(BOT_ID, bot=True)}
    chats = {CHANNEL_RAW_ID: raw_channel()}

    async def parse(update):
        return await dispatcher.update_parsers[type(update)](update, users, chats)

    message, handler = await parse(wire(T.UpdateNewEphemeralMessage(message=ephemeral(out=False))))
    assert isinstance(message, types.EphemeralMessage) and handler is pyrogram.handlers.EphemeralMessageHandler

    query, handler = await parse(wire(T.UpdateEphemeralBotCallbackQuery(
        query_id=7, user_id=USER_ID, msg_id=5, data=b"data", message=ephemeral()
    )))
    assert handler is pyrogram.handlers.CallbackQueryHandler
    assert query.data == "data" and query.message is None and query.ephemeral_message.id == 5

    deleted, handler = await parse(T.UpdateDeleteEphemeralMessages(peer=T.PeerChannel(channel_id=CHANNEL_RAW_ID),
                                                                   ids=[1, 2]))
    assert handler is pyrogram.handlers.DeletedEphemeralMessagesHandler
    assert [m.id for m in deleted] == [1, 2] and deleted[0].chat.id == CHANNEL_ID

    managed, handler = await parse(T.UpdateManagedBot(user_id=USER_ID, bot_id=BOT_ID, qts=1))
    assert handler is pyrogram.handlers.ManagedBotUpdatedHandler
    assert managed.user.id == USER_ID and managed.bot.id == BOT_ID


def test_chat_join_request_query_id():
    request = types.ChatJoinRequest._parse(
        None,
        wire(T.UpdateBotChatInviteRequester(peer=T.PeerChannel(channel_id=CHANNEL_RAW_ID), date=1, user_id=USER_ID,
                                       about="", invite=T.ChatInvitePublicJoinRequests(), qts=1, query_id=99)),
        {USER_ID: raw_user()}, {CHANNEL_RAW_ID: raw_channel()},
    )

    assert request.query_id == 99
