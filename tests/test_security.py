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

"""Regression tests for the security audit fixes."""

import asyncio
import os
import random
import stat
import time
from hashlib import sha1, sha256
from io import BytesIO
from types import SimpleNamespace

import pytest

import pyrogram
from pyrogram import enums, raw, types, utils
from pyrogram.crypto import aes, mtproto, prime, rsa
from pyrogram.errors import SecurityCheckMismatch
from pyrogram.file_id import FileId, FileType, FileUniqueId, FileUniqueType
from pyrogram.parser.parser import Parser
from pyrogram.raw.core import Message, TLObject
from pyrogram.session.auth import Auth
from pyrogram.storage import FileStorage

T = raw.types


def make_client(workdir):
    return pyrogram.Client("security", api_id=1, api_hash="0" * 32, in_memory=True, workdir=str(workdir))


# ---------------------------------------------------------------------------------------------------------------
# Path traversal in downloads
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name, expected", [
    ("report.pdf", "report.pdf"),
    ("../../etc/passwd", "passwd"),
    ("..\\..\\..\\home\\alice\\.bashrc", ".bashrc"),
    ("dir/sub\\file.txt", "file.txt"),
    ("..", ""),
    (".", ""),
    ("..\\", ""),
    ("bad\x00name\x1f.txt", "badname.txt"),
    ("", ""),
])
def test_sanitize_file_name(name, expected):
    assert utils.sanitize_file_name(name) == expected


@pytest.mark.asyncio
async def test_handle_download_refuses_to_leave_the_directory(tmp_path):
    client = make_client(tmp_path)

    for name in ("../escape.txt", os.path.join("..", "escape.txt"), "sub/../../escape.txt"):
        with pytest.raises(ValueError):
            await client.handle_download((None, str(tmp_path / "downloads"), name, False, 0, None, ()))

    assert not (tmp_path / "escape.txt").exists()


@pytest.mark.asyncio
async def test_download_media_strips_directories_from_sender_file_names(tmp_path):
    client = make_client(tmp_path)
    captured = []

    async def fake_handle_download(packet):
        captured.append(packet)

    client.handle_download = fake_handle_download

    file_id = FileId(file_type=FileType.DOCUMENT, dc_id=2, media_id=1, access_hash=2).encode()
    file_unique_id = FileUniqueId(file_unique_type=FileUniqueType.DOCUMENT, media_id=1).encode()
    document = types.Document(file_id=file_id, file_unique_id=file_unique_id,
                              file_name="..\\..\\..\\home\\alice\\.bashrc")

    await client.download_media(types.Message(id=1, document=document))

    _, directory, file_name, *_ = captured[0]
    assert file_name == ".bashrc"
    assert os.path.dirname(os.path.abspath(os.path.join(directory, file_name))) == os.path.abspath(directory)


# ---------------------------------------------------------------------------------------------------------------
# Markdown parser denial of service
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_markdown_links_parse_in_linear_time():
    parser = Parser(None)
    text = "[a](" * 1024  # 4096 characters, the maximum length of a message

    start = time.perf_counter()
    await parser.parse(text, enums.ParseMode.MARKDOWN)

    assert time.perf_counter() - start < 1  # was about 8 seconds


@pytest.mark.asyncio
async def test_markdown_links_still_parse():
    result = await Parser(None).parse("see [docs](https://example.com/a?b=1) and ![👍](tg://emoji?id=5)",
                                      enums.ParseMode.MARKDOWN)

    assert result["message"] == "see docs and 👍"
    assert [type(e) for e in result["entities"]] == [T.MessageEntityTextUrl, T.MessageEntityCustomEmoji]
    assert result["entities"][0].url == "https://example.com/a?b=1"


# ---------------------------------------------------------------------------------------------------------------
# Session file permissions
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.skipif(os.name == "nt", reason="POSIX file permissions")
@pytest.mark.asyncio
async def test_session_file_is_private(tmp_path):
    storage = FileStorage("private", tmp_path)
    await storage.open()
    await storage.close()

    assert stat.S_IMODE(os.stat(tmp_path / "private.session").st_mode) == 0o600


@pytest.mark.skipif(os.name == "nt", reason="POSIX file permissions")
@pytest.mark.asyncio
async def test_existing_readable_session_file_is_restricted(tmp_path):
    storage = FileStorage("shared", tmp_path)
    await storage.open()
    await storage.close()
    os.chmod(tmp_path / "shared.session", 0o644)

    storage = FileStorage("shared", tmp_path)
    await storage.open()
    await storage.close()

    assert stat.S_IMODE(os.stat(tmp_path / "shared.session").st_mode) == 0o600


# ---------------------------------------------------------------------------------------------------------------
# Uploading the session file by path
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("path", ["my_account.session", "/srv/bot/bot.session", "x.session-journal", "A.SESSION"])
def test_session_files_are_not_uploaded_by_path(tmp_path, path):
    with pytest.raises(ValueError):
        make_client(tmp_path)._check_uploadable_path(path)


def test_regular_files_can_be_uploaded_by_path(tmp_path):
    make_client(tmp_path)._check_uploadable_path("photo.jpg")


# ---------------------------------------------------------------------------------------------------------------
# MTProto: integrity is verified before parsing
# ---------------------------------------------------------------------------------------------------------------

AUTH_KEY = bytes(random.Random(1).getrandbits(8) for _ in range(256))
AUTH_KEY_ID = sha1(AUTH_KEY).digest()[-8:]
SESSION_ID = b"\x01" * 8


def server_packet(body: bytes, tamper_msg_key: bool = False) -> bytes:
    """Encrypt a message the way the server does (incoming direction)."""
    msg_id = (int(time.time()) << 32) | 1  # server message ids are odd
    data = b"\x00" * 8 + SESSION_ID + msg_id.to_bytes(8, "little") + (1).to_bytes(4, "little") \
        + len(body).to_bytes(4, "little") + body
    data += os.urandom(-(len(data) + 12) % 16 + 12)

    msg_key = sha256(AUTH_KEY[96:96 + 32] + data).digest()[8:24]
    aes_key, aes_iv = mtproto.kdf(AUTH_KEY, msg_key, False)

    if tamper_msg_key:
        msg_key = bytes(16)

    return AUTH_KEY_ID + msg_key + aes.ige256_encrypt(data, aes_key, aes_iv)


def test_unpack_accepts_valid_messages():
    message = mtproto.unpack(BytesIO(server_packet(T.Pong(msg_id=5, ping_id=6).write())),
                             SESSION_ID, AUTH_KEY, AUTH_KEY_ID)

    assert isinstance(message.body, T.Pong) and message.body.ping_id == 6


def test_unpack_rejects_tampered_messages_before_parsing():
    # Corrupting the last ciphertext block only garbles the padding (AES-IGE errors propagate forward), so the
    # header and the body still decrypt. The body is an unknown constructor: parsing it before the integrity check
    # would raise ValueError, verifying the integrity first raises SecurityCheckMismatch.
    packet = bytearray(server_packet(b"\xef\xbe\xad\xde" + b"\x00" * 12))
    packet[-1] ^= 0xff

    with pytest.raises(SecurityCheckMismatch):
        mtproto.unpack(BytesIO(bytes(packet)), SESSION_ID, AUTH_KEY, AUTH_KEY_ID)


def test_unpack_rejects_wrong_msg_key():
    with pytest.raises(SecurityCheckMismatch):
        mtproto.unpack(BytesIO(server_packet(T.Pong(msg_id=5, ping_id=6).write(), tamper_msg_key=True)),
                       SESSION_ID, AUTH_KEY, AUTH_KEY_ID)


def test_unpack_rejects_truncated_ciphertext():
    packet = server_packet(T.Pong(msg_id=5, ping_id=6).write())[:-3]

    with pytest.raises(SecurityCheckMismatch):
        mtproto.unpack(BytesIO(packet), SESSION_ID, AUTH_KEY, AUTH_KEY_ID)


def test_unknown_constructor_error_does_not_leak_content():
    secret = b"secret-message-content".ljust(32, b"\x00")

    with pytest.raises(ValueError) as error:
        mtproto.unpack(BytesIO(server_packet(b"\xef\xbe\xad\xde" + secret)), SESSION_ID, AUTH_KEY, AUTH_KEY_ID)

    assert str(error.value) == "The server sent an unknown constructor: 0xdeadbeef"


# ---------------------------------------------------------------------------------------------------------------
# 2FA (SRP) parameter validation
# ---------------------------------------------------------------------------------------------------------------

def srp_password(p=prime.CURRENT_DH_PRIME, g=3, B=None):
    if B is None:
        B = pow(g, random.getrandbits(2048), p)

    algo = T.PasswordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow(
        salt1=b"salt1", salt2=b"salt2", g=g, p=p.to_bytes(256, "big")
    )
    return T.account.Password(new_algo=algo, new_secure_algo=T.SecurePasswordKdfAlgoUnknown(),
                              secure_random=b"", current_algo=algo, srp_B=B.to_bytes(256, "big"), srp_id=7)


def test_srp_accepts_telegram_parameters():
    check = utils.compute_password_check(srp_password(), "password")

    assert check.srp_id == 7 and len(check.A) == 256 and len(check.M1) == 32


@pytest.mark.parametrize("password", [
    srp_password(p=prime.CURRENT_DH_PRIME - 2),  # unknown prime
    srp_password(g=2),  # generator not valid for the prime
    srp_password(B=1),  # B outside the safe range
    srp_password(B=prime.CURRENT_DH_PRIME - 1),
])
def test_srp_rejects_unsafe_parameters(password):
    with pytest.raises(SecurityCheckMismatch):
        utils.compute_password_check(password, "password")


# ---------------------------------------------------------------------------------------------------------------
# Auth key exchange against a fake Telegram server
# ---------------------------------------------------------------------------------------------------------------

def _is_probable_prime(n, rounds=20):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    for _ in range(rounds):
        x = pow(random.randrange(2, n - 1), d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _random_prime(bits):
    while True:
        candidate = random.getrandbits(bits) | (1 << (bits - 1)) | 1
        if _is_probable_prime(candidate):
            return candidate


@pytest.fixture(scope="module")
def server_rsa_key():
    """A test RSA key standing in for Telegram's server key."""
    e = 65537
    while True:
        p, q = _random_prime(1024), _random_prime(1024)
        n, phi = p * q, (p - 1) * (q - 1)
        if n.bit_length() == 2048 and phi % e:
            return n, e, pow(e, -1, phi)


def rsa_pad_decrypt(encrypted_data: bytes, rsa_key) -> bytes:
    """Undo RSA_PAD the way the server does, verifying its hash; returns the padded inner data."""
    n, _, d = rsa_key
    key_aes_encrypted = pow(int.from_bytes(encrypted_data, "big"), d, n).to_bytes(256, "big")
    temp_key_xor, aes_encrypted = key_aes_encrypted[:32], key_aes_encrypted[32:]
    temp_key = bytes(a ^ b for a, b in zip(temp_key_xor, sha256(aes_encrypted).digest()))

    data_with_hash = aes.ige256_decrypt(aes_encrypted, temp_key, bytes(32))
    data_with_padding = data_with_hash[:192][::-1]
    assert data_with_hash[192:] == sha256(temp_key + data_with_padding).digest(), "RSA_PAD hash mismatch"

    return data_with_padding


@pytest.mark.parametrize("length", [0, 1, 100, 144])
def test_rsa_pad_round_trip(server_rsa_key, monkeypatch, length):
    monkeypatch.setattr(rsa, "server_public_keys", {1: rsa.PublicKey(server_rsa_key[0], server_rsa_key[1])})
    data = os.urandom(length)

    encrypted = rsa.pad_and_encrypt(data, 1)

    assert len(encrypted) == 256
    assert rsa_pad_decrypt(encrypted, server_rsa_key)[:length] == data
    assert rsa.pad_and_encrypt(data, 1) != encrypted  # randomized: a new temporary key and padding every time


def test_rsa_pad_rejects_oversized_data(server_rsa_key, monkeypatch):
    monkeypatch.setattr(rsa, "server_public_keys", {1: rsa.PublicKey(server_rsa_key[0], server_rsa_key[1])})

    with pytest.raises(ValueError):
        rsa.pad_and_encrypt(bytes(145), 1)


class FakeTelegramServer:
    """Plays the server side of https://core.telegram.org/mtproto/auth_key over a fake connection."""

    FINGERPRINT = 1234567890

    def __init__(self, rsa_key, mode="ok"):
        self.n, self.e, self.d = rsa_key
        self.mode = mode
        self.received = []
        self.auth_key = None

    # Connection interface used by Auth
    async def connect(self):
        pass

    async def close(self):
        pass

    async def send(self, packet: bytes):
        self.received.append(TLObject.read(BytesIO(packet[20:])))

    async def recv(self) -> bytes:
        return bytes(20) + self.respond(self.received[-1]).write()

    def respond(self, request):
        if isinstance(request, raw.functions.ReqPqMulti):
            self.nonce = request.nonce
            self.server_nonce = int.from_bytes(os.urandom(16), "little", signed=True)
            pq = 2 ** 70 + 1 if self.mode == "huge_pq" else _random_prime(31) * _random_prime(31)
            return T.ResPQ(nonce=self.nonce, server_nonce=self.server_nonce,
                           pq=pq.to_bytes((pq.bit_length() + 7) // 8, "big"),
                           server_public_key_fingerprints=[self.FINGERPRINT])

        if isinstance(request, raw.functions.ReqDHParams):
            inner = TLObject.read(BytesIO(rsa_pad_decrypt(request.encrypted_data, (self.n, self.e, self.d))))
            assert isinstance(inner, T.PQInnerDataDc)
            self.inner_dc = inner.dc

            new_nonce = inner.new_nonce.to_bytes(32, "little", signed=True)
            server_nonce = self.server_nonce.to_bytes(16, "little", signed=True)
            self.new_nonce = new_nonce
            self.tmp_key = sha1(new_nonce + server_nonce).digest() + sha1(server_nonce + new_nonce).digest()[:12]
            self.tmp_iv = (sha1(server_nonce + new_nonce).digest()[12:] + sha1(new_nonce + new_nonce).digest()
                           + new_nonce[:4])

            dh_prime = prime.CURRENT_DH_PRIME if self.mode != "bad_prime" else prime.CURRENT_DH_PRIME - 2
            self.a = int.from_bytes(os.urandom(256), "big")
            g_a = pow(3, self.a, prime.CURRENT_DH_PRIME)

            answer = T.ServerDHInnerData(nonce=self.nonce, server_nonce=self.server_nonce, g=3,
                                         dh_prime=dh_prime.to_bytes(256, "big"), g_a=g_a.to_bytes(256, "big"),
                                         server_time=int(time.time())).write()
            answer_with_hash = sha1(answer).digest() + answer
            answer_with_hash += os.urandom(-len(answer_with_hash) % 16)

            return T.ServerDHParamsOk(nonce=self.nonce, server_nonce=self.server_nonce,
                                      encrypted_answer=aes.ige256_encrypt(answer_with_hash, self.tmp_key, self.tmp_iv))

        if isinstance(request, raw.functions.SetClientDHParams):
            decrypted = aes.ige256_decrypt(request.encrypted_data, self.tmp_key, self.tmp_iv)
            inner = TLObject.read(BytesIO(decrypted[20:]))
            self.auth_key = pow(int.from_bytes(inner.g_b, "big"), self.a, prime.CURRENT_DH_PRIME).to_bytes(256, "big")

            if self.mode == "gen_fail":
                return T.DhGenFail(nonce=self.nonce, server_nonce=self.server_nonce, new_nonce_hash3=0)

            aux_hash = sha1(self.auth_key).digest()[:8]
            new_nonce_hash1 = int.from_bytes(sha1(self.new_nonce + b"\x01" + aux_hash).digest()[4:20],
                                             "little", signed=True)
            if self.mode == "bad_hash":
                new_nonce_hash1 ^= 1

            return T.DhGenOk(nonce=self.nonce, server_nonce=self.server_nonce, new_nonce_hash1=new_nonce_hash1)

        raise AssertionError(f"unexpected request {request}")


@pytest.fixture
def fake_server_auth(server_rsa_key, monkeypatch):
    monkeypatch.setattr(rsa, "server_public_keys",
                        {FakeTelegramServer.FINGERPRINT: rsa.PublicKey(server_rsa_key[0], server_rsa_key[1])})
    monkeypatch.setattr(Auth, "MAX_RETRIES", 0)

    def make(mode, test_mode=False):
        server = FakeTelegramServer(server_rsa_key, mode)
        client = SimpleNamespace(ipv6=False, alt_port=False, proxy=None, protocol_factory=None,
                                 connection_factory=lambda **kwargs: server)
        return Auth(client, dc_id=2, test_mode=test_mode), server

    return make


@pytest.mark.asyncio
async def test_auth_key_exchange_succeeds(fake_server_auth):
    auth, server = fake_server_auth("ok")

    auth_key = await auth.create()

    assert len(auth_key) == 256 and auth_key == server.auth_key
    assert server.inner_dc == 2


@pytest.mark.asyncio
async def test_auth_key_exchange_names_the_test_dc(fake_server_auth):
    auth, server = fake_server_auth("ok", test_mode=True)

    await auth.create()

    assert server.inner_dc == 10002


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["bad_hash", "gen_fail"])
async def test_auth_key_exchange_requires_key_confirmation(fake_server_auth, mode):
    auth, _ = fake_server_auth(mode)

    with pytest.raises(SecurityCheckMismatch):
        await auth.create()


@pytest.mark.asyncio
async def test_bad_dh_parameters_are_rejected_before_sending_g_b(fake_server_auth):
    auth, server = fake_server_auth("bad_prime")

    with pytest.raises(SecurityCheckMismatch):
        await auth.create()

    assert not any(isinstance(r, raw.functions.SetClientDHParams) for r in server.received)


@pytest.mark.asyncio
async def test_oversized_pq_is_rejected_instead_of_factorized(fake_server_auth):
    auth, _ = fake_server_auth("huge_pq")

    with pytest.raises(SecurityCheckMismatch):
        await asyncio.wait_for(auth.create(), timeout=10)
