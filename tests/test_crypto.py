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

"""Tests for the AES implementation used when TgCrypto isn't installed.

The expected values were produced with TgCrypto, an independent C implementation.
"""

import random

import pytest

from pyrogram.crypto import aes

KEY = bytes(range(32))
IGE_IV = bytes(range(32, 64))
DATA = bytes(range(64))

IGE_ENCRYPTED = bytes.fromhex(
    "42e66e1a756cccf5b27acc47523ad074ee39bf54e3db37bbdf415df6b400fca9"
    "77f708327c9e9341cc3dc8efd31e76463daa65b1f0d0252f790d77f1824a662c"
)

# CTR starting two blocks before the 128-bit counter wraps around, fed in three uneven chunks
CTR_IV = b"\xff" * 15 + b"\xfe"
CTR_ENCRYPTED = bytes.fromhex(
    "63e4b601b11b4edaf2e4f3d595c1294bf988f60e58b266cd4b9e0b60419249f1"
    "d2b122950e6cb9f781dab041f10359afc06c449d7e8ca9d29ecfa10a74ff0802"
)
CTR_FINAL_IV = bytes.fromhex("00000000000000000000000000000002")


def test_ige_matches_known_answer():
    assert aes._ige256_encrypt(DATA, KEY, IGE_IV) == IGE_ENCRYPTED
    assert aes._ige256_decrypt(IGE_ENCRYPTED, KEY, IGE_IV) == DATA


def test_ctr_matches_known_answer_across_chunks():
    iv, state = bytearray(CTR_IV), bytearray(1)

    out = b"".join(aes._ctr256_encrypt(chunk, KEY, iv, state) for chunk in (DATA[:5], DATA[5:40], DATA[40:]))

    assert out == CTR_ENCRYPTED
    assert bytes(iv) == CTR_FINAL_IV and state[0] == 0


def test_ctr_chunking_does_not_change_the_stream():
    rng = random.Random(7)

    for _ in range(50):
        key, start_iv = rng.randbytes(32), rng.randbytes(16)
        stream = rng.randbytes(rng.randint(1, 300))

        whole = aes._ctr256_encrypt(stream, key, bytearray(start_iv), bytearray(1))

        iv, state, parts, position = bytearray(start_iv), bytearray(1), [], 0
        while position < len(stream):
            size = rng.randint(1, 40)
            parts.append(aes._ctr256_encrypt(stream[position:position + size], key, iv, state))
            position += size

        assert b"".join(parts) == whole
        assert aes._ctr256_decrypt(whole, key, bytearray(start_iv), bytearray(1)) == stream


def test_ige_round_trip():
    rng = random.Random(9)

    for _ in range(50):
        key, iv, data = rng.randbytes(32), rng.randbytes(32), rng.randbytes(16 * rng.randint(1, 20))
        assert aes._ige256_decrypt(aes._ige256_encrypt(data, key, iv), key, iv) == data


def test_matches_tgcrypto_when_installed():
    tgcrypto = pytest.importorskip("tgcrypto")
    rng = random.Random(11)

    for _ in range(100):
        key, iv32, data = rng.randbytes(32), rng.randbytes(32), rng.randbytes(16 * rng.randint(1, 20))
        assert aes._ige256_encrypt(data, key, iv32) == tgcrypto.ige256_encrypt(data, key, iv32)

        iv16 = rng.randbytes(16)
        ours, theirs = (bytearray(iv16), bytearray(1)), (bytearray(iv16), bytearray(1))
        assert aes._ctr256_encrypt(data, key, *ours) == tgcrypto.ctr256_encrypt(data, key, *theirs)
        assert ours == theirs
