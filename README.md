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

Changes compared to Pyrofork 2.3.69 (Telegram API layer 223).

#### Telegram API layer 229

- Updated the Telegram API schema from layer 223 to layer 229, adding about 185 new types and methods (communities,
  rich messages, ephemeral messages, AI compose tones, web browser settings and more), available through `pyrogram.raw`.
- Keyboards follow Telegram's new button model. `InlineKeyboardButton`, `KeyboardButton`, `LoginUrl` and
  `InlineKeyboardButtonBuy` work exactly as before; only the underlying raw types changed.
- `send_poll` and `stop_poll` send the poll `hash` that Telegram now requires, and quiz answers are sent as option
  indexes. Missing vote counts in poll results are treated as 0.
- `join_chat` understands Telegram's new join result, including chats protected by a guard bot.

#### Bug fixes

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
