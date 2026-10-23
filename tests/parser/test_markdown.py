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

"""Markdown.unparse escapes text that would read as markup, so Message.text.markdown can be sent again safely"""

import pytest

from pyrogram import enums, raw, types
from pyrogram.parser.markdown import Markdown
from pyrogram.parser.parser import Parser

E = enums.MessageEntityType


def entity(entity_type, offset, length, **kwargs):
    return types.MessageEntity(type=entity_type, offset=offset, length=length, **kwargs)


ROUND_TRIPS = [
    # Plain text that looks like markup: it used to come back as formatting, links or a mention
    ("**not bold** and __not italic__ --u-- ~~s~~ ||sp||", []),
    ("[free](tg://user?id=1) ![x](tg://emoji?id=5)", []),
    ("> not a quote\n> still not", []),
    ("a `b` c ```pre```", []),
    ("C:\\path\\*x \\\\ end\\", []),
    # Delimiter characters next to formatting don't join its delimiters
    ("a*", [entity(E.BOLD, 0, 2)]),
    ("x**y", [entity(E.ITALIC, 1, 2)]),
    ("wow!link", [entity(E.TEXT_LINK, 4, 4, url="https://example.com")]),
    ("😀 **x** 😀", [entity(E.BOLD, 3, 5)]),
    # The default mode used to turn " > " inside a quote into " >" (HTML.parse took "<blockquote>quote >" for a tag)
    ("quote > x\n> more", [entity(E.BLOCKQUOTE, 0, 16)]),
    # Code keeps its text as it is
    ("code \\* x **", [entity(E.CODE, 5, 7)]),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [enums.ParseMode.MARKDOWN, enums.ParseMode.DEFAULT])
@pytest.mark.parametrize("text, entities", ROUND_TRIPS)
async def test_unparsed_markdown_parses_back_to_the_same_message(text, entities, mode):
    result = await Parser(None).parse(Markdown.unparse(text, entities), mode)

    assert result["message"] == text
    assert [(e.offset, e.length) for e in result["entities"] or []] == [(e.offset, e.length) for e in entities]


def test_ordinary_text_and_formatting_are_not_escaped():
    text = "well-known my_bot x*y wow! (ok) bold"

    assert Markdown.unparse(text, [entity(E.BOLD, 32, 4)]) == "well-known my_bot x*y wow! (ok) **bold**"


@pytest.mark.asyncio
async def test_escaped_characters_are_plain_text():
    result = await Parser(None).parse(r"\*\*x\*\* \[a\](https://example.com) \`y\` \\", enums.ParseMode.MARKDOWN)

    assert result["message"] == "**x** [a](https://example.com) `y` \\"
    assert not result["entities"]


@pytest.mark.asyncio
async def test_backslashes_in_code_are_kept():
    result = await Parser(None).parse(r"`a\*b` ```py" "\n" r"print('\\n')" "\n```", enums.ParseMode.MARKDOWN)

    assert result["message"].startswith(r"a\*b")
    assert r"print('\\n')" in result["message"]
    assert [type(e) for e in result["entities"]] == [raw.types.MessageEntityCode, raw.types.MessageEntityPre]
