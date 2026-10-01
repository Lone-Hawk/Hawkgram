<p align="center">
    <b>Telegram MTProto API Framework for Python</b>
    <br>
    <a href="https://github.com/Lone-Hawk/Hawkgram">
        Source
    </a>
    •
    <a href="https://github.com/Lone-Hawk/Hawkgram/issues">
        Issues
    </a>
</p>

## Hawkgram

> Elegant, modern and asynchronous Telegram MTProto API framework in Python for users and bots

``` python
from pyrogram import Client, filters

app = Client("my_account")


@app.on_message(filters.private)
async def hello(client, message):
    await message.reply("Hello from Hawkgram!")


app.run()
```

**Hawkgram** is a modern, elegant and asynchronous MTProto API
framework. It enables you to easily interact with the main Telegram API through a user account (custom client) or a bot
identity (bot API alternative) using Python.

### Key Features

- **Ready**: Install Hawkgram with pip and start building your applications right away.
- **Easy**: Makes the Telegram API simple and intuitive, while still allowing advanced usages.
- **Elegant**: Low-level details are abstracted and re-presented in a more convenient way.
- **Fast**: Boosted up by [TgCrypto](https://github.com/pyrogram/tgcrypto), a high-performance cryptography library written in C.  
- **Type-hinted**: Types and methods are all type-hinted, enabling excellent editor support.
- **Async**: Fully asynchronous (also usable synchronously if wanted, for convenience).
- **Powerful**: Full access to Telegram's API to execute any official client action and more.

### Installing

``` bash
pip3 install hawkgram
```

Hawkgram keeps the `pyrogram` import name, so existing code keeps working unchanged.

### Changelog

#### Hawkgram 1.0.2: maintained dependencies

- **`pyaes` replaced with `cryptography`.** When TgCrypto isn't installed, AES now runs in compiled code from the
  actively maintained `cryptography` package instead of the unmaintained pure-Python `pyaes` (last release 2017).
  The output is identical to before.
- **`pysocks` replaced with `python-socks`.** Proxy connections (SOCKS4, SOCKS5 and HTTP) use the maintained
  `python-socks` package instead of `pysocks` (last release 2019). The proxy handshake no longer blocks the client
  while it waits. Proxy settings are unchanged.
- The forked `tgcrypto-pyrofork` and `pymediainfo-pyrofork` dependencies are capped at their latest reviewed
  releases, so a new release is only installed after it has been reviewed.

Reinstall Hawkgram after updating so the new dependencies are installed.

#### Hawkgram 1.0.1: security fixes

All the issues below were inherited from Pyrofork. Updating is strongly recommended, especially on Linux and macOS.

- **Downloads could write files anywhere (Linux and macOS).** A document whose file name contained backslashes
  could be saved outside the download folder, overwriting any file the program can write. File names from other
  users are now reduced to a single component, and downloads can never leave their target folder.
- **Messages could freeze the client.** A crafted 4096-character text took about 8 seconds to parse as Markdown,
  blocking all handlers; it now takes milliseconds.
- **Session files were readable by other users of the computer (Linux and macOS).** They are now created, and
  tightened if needed, with owner-only permissions.
- **Session files are never uploaded by path**, so a bot passing user input to `send_document` and similar methods
  can't be tricked into sending its own session.
- **Stricter protocol checks:** the integrity of incoming messages is verified before they are parsed, the auth key
  exchange validates the server's answer before sending anything and requires the server's key confirmation, 2FA
  only accepts Telegram's known safe parameters, and every incoming message is checked against the clock.
- **Logs no longer contain secrets:** debug logs record request and response types instead of their contents.
- Hardened CI: pinned actions, read-only permissions, and building separated from publishing.

**Hawkgram 1.0.0**, the first release. Changes compared to Pyrofork 2.3.69 (Telegram API layer 223).

#### Telegram API layer 229

- Updated the Telegram API schema from layer 223 to layer 229, adding about 185 new types and methods (communities,
  rich messages, ephemeral messages, AI compose tones, web browser settings and more), available through `pyrogram.raw`.
- Keyboards follow Telegram's new button model. `InlineKeyboardButton`, `KeyboardButton`, `LoginUrl` and
  `InlineKeyboardButtonBuy` work exactly as before; only the underlying raw types changed.
- `send_poll` and `stop_poll` send the poll `hash` that Telegram now requires, and quiz answers are sent as option
  indexes. Missing vote counts in poll results are treated as 0.
- `join_chat` understands Telegram's new join result, including chats protected by a guard bot.

#### New features

- **Communities**: groups of supergroups, channels and bots. Create them, list the ones you joined, manage requests to
  add chats, hide or remove chats, ban members and collapse them in the chat list. Communities are regular `Chat`
  objects (`ChatType.COMMUNITY`), and `get_chat` returns their chats and description.
- **Ephemeral messages**: messages visible to a single user of a chat. Send, edit and delete them, manage the welcome
  messages shown to new members, and handle them with `on_ephemeral_message`, `on_edited_ephemeral_message` and
  `on_deleted_ephemeral_messages`. Button clicks on ephemeral messages arrive in `on_callback_query`.
- **AI compose**: rewrite, proofread, translate or emojify texts with `compose_text_with_ai`, manage built-in and custom
  tones, and pass a tone to `translate_message_text`.
- **Rich messages**: send and edit messages with headings, lists, tables and formulas from HTML or Markdown, translate
  or compose them with AI, read them from `Message.rich_message`, and send them as inline results.
- **Polls**: new `send_poll` options (revoting, shuffled options, results hidden until closed, options added by users,
  members-only and country limits), adding and deleting options, unread votes and `MessagesFilter.POLL`.
- **Bots**: create managed bots and manage their tokens and access, guard new members of a group with
  `answer_chat_join_query` and `set_chat_join_requests`, and answer guest chat queries with `on_guest_chat_query`.
- Web browser settings, removing the reactions of a chat member, the messages of a user's personal channel, and new
  service messages for communities, managed bots and poll options.

#### Bug fixes

- Requests with an empty list in an optional field were malformed, which could make Telegram reject them.
- Texts proofread by AI couldn't be parsed.
- `on_purchased_paid_media` crashed when used, and to-do completion messages had no service type.

- Methods that failed on every call now work:
  - all forum topic methods (`create_forum_topic`, `edit_forum_topic`, `close_forum_topic`, `get_forum_topics`, ...)
  - `transfer_chat_ownership`
  - `delete_scheduled_messages`
  - `update_color` for your own profile
  - `set_gift_resale_price`
  - `get_chat_gifts`, `get_chat_gifts_count` and `get_business_account_gifts`
- `send_media_group`, `copy_media_group` and `send_paid_media` sent the messages but then crashed instead of
  returning them.
- Inline buttons with a `login_url` raised an error when sent.
- Parsing no longer crashes on Stars transactions (including Fragment and App Store sources), gifted Premium and gift
  codes, business bot connections, shipping addresses, solid color and gradient wallpapers, saved gifts and Stars
  status.
- Fixed values that were always empty: the link returned by `export_folder_link`, chat wallpaper flags, story view
  counts and chat theme emoji.

#### Behavior changes

- `join_chat` returns `None` when the join must first be approved by the chat's guard bot.
- `delete_scheduled_messages` returns the IDs of the messages Telegram reports as deleted.
- `transfer_chat_ownership` also works for basic groups, not only supergroups and channels.
- The app version shown in Telegram's active sessions list is now `Hawkgram x.y.z`.

#### Project

- Renamed to Hawkgram and published as `hawkgram`; the `pyrogram` import name is unchanged.
- License headers name Hawkgram and Lone Hawk. All original copyright notices are kept, and the license is still
  LGPL-3.0-or-later.
- Removed Pyrofork links, the funding file and the deployment to Pyrofork's documentation site.
- `.gitignore` no longer excludes the documentation sources, the unused `MANIFEST.in` is gone, and the docs no longer
  reference missing logo files.
- All tests pass.

### Credits

Hawkgram is developed by Lone Hawk. It is based on Pyrofork by Mayuri-Chan, which is itself a fork of Pyrogram by Dan.
