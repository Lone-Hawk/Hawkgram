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

import logging

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

log = logging.getLogger(__name__)


def xor(a: bytes, b: bytes) -> bytes:
    return int.to_bytes(
        int.from_bytes(a, "big") ^ int.from_bytes(b, "big"),
        len(a),
        "big",
    )


# Implementation based on the "cryptography" package, used when TgCrypto isn't installed.
# AES itself runs in compiled code; the IGE chaining and the CTR bookkeeping are done here.

def _ige(data: bytes, key: bytes, iv: bytes, encrypt: bool) -> bytes:
    # MTProto mandates AES-IGE, which "cryptography" doesn't offer. ECB is used here only as the raw AES block
    # function: every block is chained through iv_1 and iv_2 below, so ECB's pattern leakage doesn't apply.
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    aes = cipher.encryptor() if encrypt else cipher.decryptor()

    iv_1 = iv[:16]
    iv_2 = iv[16:]

    data = [data[i: i + 16] for i in range(0, len(data), 16)]

    if encrypt:
        for i, chunk in enumerate(data):
            iv_1 = data[i] = xor(aes.update(xor(chunk, iv_1)), iv_2)
            iv_2 = chunk
    else:
        for i, chunk in enumerate(data):
            iv_2 = data[i] = xor(aes.update(xor(chunk, iv_2)), iv_1)
            iv_1 = chunk

    return b"".join(data)


def _ctr(data: bytes, key: bytes, iv: bytearray, state: bytearray) -> bytes:
    """AES-256-CTR over a stream split across calls.

    *iv* is the current 128-bit big-endian counter block and *state[0]* the offset within its keystream block.
    Both are updated in place, like TgCrypto does, so consecutive calls continue the same keystream.
    """
    offset = state[0]

    keystream = Cipher(algorithms.AES(key), modes.CTR(bytes(iv))).encryptor().update(bytes(offset + len(data)))
    keystream = keystream[offset:]

    out = (int.from_bytes(data, "big") ^ int.from_bytes(keystream, "big")).to_bytes(len(data), "big")

    blocks_used, state[0] = divmod(offset + len(data), 16)
    iv[:] = ((int.from_bytes(iv, "big") + blocks_used) % (1 << 128)).to_bytes(16, "big")

    return out


def _ige256_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    return _ige(data, key, iv, True)


def _ige256_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    return _ige(data, key, iv, False)


def _ctr256_encrypt(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
    return _ctr(data, key, iv, state or bytearray(1))


def _ctr256_decrypt(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
    return _ctr(data, key, iv, state or bytearray(1))


try:
    import tgcrypto

    log.info("Using TgCrypto")

    def ige256_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
        return tgcrypto.ige256_encrypt(data, key, iv)

    def ige256_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
        return tgcrypto.ige256_decrypt(data, key, iv)

    def ctr256_encrypt(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
        return tgcrypto.ctr256_encrypt(data, key, iv, state or bytearray(1))

    def ctr256_decrypt(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
        return tgcrypto.ctr256_decrypt(data, key, iv, state or bytearray(1))
except ImportError:
    log.warning(
        "TgCrypto is missing! "
        "Hawkgram will work the same, but at a much slower speed."
    )

    ige256_encrypt = _ige256_encrypt
    ige256_decrypt = _ige256_decrypt
    ctr256_encrypt = _ctr256_encrypt
    ctr256_decrypt = _ctr256_decrypt
