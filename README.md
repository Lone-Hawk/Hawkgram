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

#### Hawkgram 1.0.9 (unreleased): security review fixes

- **`Message.text.html` and `.caption.html` escape all of the text.** Text before, after or outside of any formatting
  was returned as is, so a user who typed `<b>` or `<a href="tg://user?id=…">` got real formatting and mentions when a
  bot sent the result again with HTML parsing (and HTML injection if it was shown on a web page). A code block's
  language and a link's URL are now escaped too, so they can't break out of their attribute.
- **Clients using MongoDB sessions can upload files by path again.** Since 1.0.1 the session file check raised
  `TypeError` for every `send_document`, `send_photo`, etc. given a file path when `mongodb=` was used.
- **Failed downloads are no longer saved as complete files.** When a download broke off (a lost connection, an error
  from Telegram) or a part from Telegram's CDN failed its integrity check, `download_media` saved what it had as if
  it were the whole file and returned its path. It now deletes the partial file, logs the error and returns `None`,
  as documented. `stream_media` raises the error instead of silently ending early.
- **Requests retried after a `BadMsgNotification` return their real result.** The notification itself was returned
  as the answer, so the method failed with an unrelated error (or `IndexError`) even when the retry worked. If the
  server keeps rejecting the request, `BadMsgNotification` is raised.
- **`delete_messages` only deletes messages of the chat you give it.** Private chats and basic groups share one
  sequence of message ids, and Telegram's delete request for them names no chat, so `delete_messages(chat_id, 6)`
  deleted message 6 wherever it was. A bot that checked a user's rights in one group could be made to delete a
  message in another. Ids of messages in other chats are now ignored (this costs one extra request).
- **`send_payment_form` no longer fails after the stars are spent.** Reading the result raised `AttributeError` or
  `KeyError` for some answers, or returned `None`, although the payment had gone through, so a caller retrying the
  "failed" call paid again. It now always returns the list of bought photos and videos, which is empty when the
  invoice isn't for paid media, and it reads all of them instead of only the first message's.
- **`transfer_gift` and `upgrade_gift` no longer spend Stars unless you allow it** (behaviour change). When Telegram
  asked for payment, they paid whatever the price was, without saying so. Now they raise `PaymentRequired` by default;
  pass `max_star_count` (also on `Gift.transfer` and `Gift.upgrade`) to pay up to that many Stars. A higher price, or
  one that isn't in Stars, raises `ValueError` and nothing is paid.
- **Busy clients write their session file far less often.** Every incoming update was committed (and synced to disk)
  to the `.session` file on its own, several times, blocking the client meanwhile. Peers and update states are now
  committed together at most once a second, and when the client stops.
- **Downloads and uploads reuse their connections.** Every file opened a new connection, and a file stored in
  another data center also needed a new encryption key and a new login there, every time, which made each transfer
  slower and could run into Telegram's rate limits. One connection per data center is now kept until the client stops,
  and shared with inline message edits. A connection whose login to another data center failed is no longer kept
  (inline edits on that data center used to keep failing).
- `sleep_threshold` passed to `invoke` now also applies after a request was retried because of a network error;
  the retry used to fall back to the default threshold and wait out flood waits you asked to receive.
- A private or group message that arrives in short form no longer raises `AttributeError` in the update task when
  Telegram has nothing more to send for it (an empty or too long difference).
- `leave_chat` forgets a channel's update state only after the channel was left, and also when it was given a
  username or link. The state used to be looked up by the `chat_id` as given (so usernames never matched), removed
  before leaving even if leaving failed, and only with `skip_updates=False`.
- **`delete_chat_history` no longer deletes a whole channel history when given a date range.** `min_date`,
  `max_date` and `just_clear` were ignored for channels and supergroups, so the whole history up to `max_id` was
  deleted; they now raise `ValueError` there. The number of deleted messages is counted from all of Telegram's
  updates instead of raising `IndexError` (after deleting) when there were none.
- **MongoDB sessions: `log_out` really deletes the session.** Errors while deleting were silently ignored, and
  `remove_peers=True` never removed anything (it used `remove()`, which current MongoDB drivers don't have). Peers
  and usernames are now removed when asked, the update states always, and errors are raised.
- **Downloads with problem names work on Windows.** File names chosen by the sender with characters Windows doesn't
  allow (`<>:"|?*`) made the download fail, trailing dots and spaces were silently dropped, and device names such as
  `CON` or `NUL.zip` sent the file to a device; these names are now adjusted. Two downloads with the same name at the
  same time no longer share a temporary file (one used to fail or truncate the other).

#### Hawkgram 1.0.8: folder links

- **`export_folder_link` returns the new link.** It raised `NameError` after Telegram had already created the link,
  so the call failed even though the link existed.
- **Folder links share the right chats.** A folder's pinned and included chats are each shared once, and its excluded
  chats never are. Folders with excluded or pinned chats used to send their included chats two or three times, and
  pinned chats were left out of the link.

#### Hawkgram 1.0.7: Python 3.14 event loops

- **A client created outside of a running event loop works with `asyncio.run`.** A client defined at module level
  and started inside `asyncio.run(main())` now runs on that loop. Its update workers used to be scheduled on another
  loop that never ran, so handlers never fired and `listen`/`wait_for_message` failed with "attached to a different
  loop".
- **Handlers added before the loop starts are registered at once**, e.g. with `@app.on_message()` at import time.
  They used to wait for a task on the loop the client was created with, so they were lost when the client was
  started with `asyncio.run`. Removing a handler that doesn't exist now raises `ValueError` right away.
- **`app.run()` no longer depends on a current event loop.** Since Python 3.14 `asyncio` no longer creates one
  implicitly, so `app.run()` raised `RuntimeError` when `asyncio.run()` had been used between creating the client and
  running it. A new loop is created when there's none, or when the current one is closed.
- Callback query handlers no longer use `asyncio.iscoroutinefunction`, which is deprecated since Python 3.14.

#### Hawkgram 1.0.6: messages with formatted dates

- **Messages with a formatted date are no longer dropped.** `MessageEntityType` was missing `FORMATTED_DATE`, so
  parsing any message that contained one raised `ValueError` and the update never reached a handler. The entity now
  has its own type, exposes the shown point in time as `MessageEntity.date`, and keeps its display format when the
  message is sent again.
- **A message entity of an unknown type no longer makes the whole message unparsable.** Entity types added by a newer
  API layer are parsed as `MessageEntityType.UNKNOWN`.

#### Hawkgram 1.0.5: bounded unknown_errors.txt

- **`unknown_errors.txt` no longer grows without limit.** When it reaches 1 MiB it is moved to
  `unknown_errors.txt.1`, replacing the previous one, so the two files take about 2 MiB at most and the latest errors
  are always kept.
- **Unknown Telegram errors are no longer lost** when `unknown_errors.txt` can't be written, for example in a read-only
  folder. The write failure used to replace the error itself; now the error is raised as usual.

#### Hawkgram 1.0.4: current key exchange encryption

- **The auth key exchange uses RSA_PAD**, Telegram's current scheme for encrypting the data sent to the server when a
  new session key is created. The data is wrapped in AES-256-IGE under a random temporary key with a SHA-256 hash
  before the RSA encryption, replacing the older RSA of a SHA-1 hash, the data and random padding.
- The key exchange names the data center the key is created for (`p_q_inner_data_dc`), as Telegram's documentation
  requires together with RSA_PAD.
- Telegram's current production and test server keys are included and always preferred, since Telegram only accepts
  RSA_PAD with them. Test mode (`test_mode=True`) uses the test servers' key, which was missing.
- When Telegram rejects the key exchange, the error names the server's error code instead of `KeyError: 0`.
- Verified by creating new session keys on all five production data centers and on the test servers. Existing
  sessions are not affected.

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
