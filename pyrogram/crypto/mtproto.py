#  Hawkgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#  Copyright (C) 2022-present Mayuri-Chan <https://github.com/Mayuri-Chan>
#  Copyright (C) 2026-present Lone Hawk
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

import hmac
from hashlib import sha256
from io import BytesIO
from os import urandom

from pyrogram.errors import SecurityCheckMismatch
from pyrogram.raw.core import Message, Long
from . import aes


def kdf(auth_key: bytes, msg_key: bytes, outgoing: bool) -> tuple:
    # https://core.telegram.org/mtproto/description#defining-aes-key-and-initialization-vector
    x = 0 if outgoing else 8

    sha256_a = sha256(msg_key + auth_key[x: x + 36]).digest()
    sha256_b = sha256(auth_key[x + 40:x + 76] + msg_key).digest()  # 76 = 40 + 36

    aes_key = sha256_a[:8] + sha256_b[8:24] + sha256_a[24:32]
    aes_iv = sha256_b[:8] + sha256_a[8:24] + sha256_b[24:32]

    return aes_key, aes_iv


def pack(message: Message, salt: int, session_id: bytes, auth_key: bytes, auth_key_id: bytes) -> bytes:
    data = Long(salt) + session_id + message.write()
    padding = urandom(-(len(data) + 12) % 16 + 12)

    # 88 = 88 + 0 (outgoing message)
    msg_key_large = sha256(auth_key[88: 88 + 32] + data + padding).digest()
    msg_key = msg_key_large[8:24]
    aes_key, aes_iv = kdf(auth_key, msg_key, True)

    return auth_key_id + msg_key + aes.ige256_encrypt(data + padding, aes_key, aes_iv)


def unpack(
    b: BytesIO,
    session_id: bytes,
    auth_key: bytes,
    auth_key_id: bytes
) -> Message:
    SecurityCheckMismatch.check(b.read(8) == auth_key_id, "b.read(8) == auth_key_id")

    msg_key = b.read(16)
    encrypted_data = b.read()

    # AES-IGE works on whole 16-byte blocks; anything else can't be a valid message
    SecurityCheckMismatch.check(
        len(encrypted_data) > 0 and len(encrypted_data) % 16 == 0,
        "len(encrypted_data) > 0 and len(encrypted_data) % 16 == 0"
    )

    aes_key, aes_iv = kdf(auth_key, msg_key, False)
    decrypted_data = aes.ige256_decrypt(encrypted_data, aes_key, aes_iv)

    # The integrity of the message is verified before any of its content is parsed or used
    # https://core.telegram.org/mtproto/security_guidelines#checking-sha256-hash-value-of-msg-key
    # 96 = 88 + 8 (incoming message)
    SecurityCheckMismatch.check(
        hmac.compare_digest(msg_key, sha256(auth_key[96:96 + 32] + decrypted_data).digest()[8:24]),
        "msg_key == sha256(auth_key[96:96 + 32] + decrypted_data).digest()[8:24]"
    )

    data = BytesIO(decrypted_data)
    data.read(8)  # Salt

    # https://core.telegram.org/mtproto/security_guidelines#checking-session-id
    SecurityCheckMismatch.check(data.read(8) == session_id, "data.read(8) == session_id")

    try:
        message = Message.read(data)
    except KeyError as e:
        if e.args[0] == 0:
            raise ConnectionError("Received empty data. Check your internet connection.")

        # Only the constructor is reported: the message content is private data and must not end up in logs
        raise ValueError(f"The server sent an unknown constructor: {hex(e.args[0])}")

    # https://core.telegram.org/mtproto/security_guidelines#checking-message-length
    data.seek(32)  # Get to the payload, skip salt (8) + session_id (8) + msg_id (8) + seq_no (4) + length (4)
    payload = data.read()
    padding = payload[message.length:]
    SecurityCheckMismatch.check(12 <= len(padding) <= 1024, "12 <= len(padding) <= 1024")
    SecurityCheckMismatch.check(len(payload) % 4 == 0, "len(payload) % 4 == 0")

    # https://core.telegram.org/mtproto/security_guidelines#checking-msg-id
    SecurityCheckMismatch.check(message.msg_id % 2 != 0, "message.msg_id % 2 != 0")

    return message
