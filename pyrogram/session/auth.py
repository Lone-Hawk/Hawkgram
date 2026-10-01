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

import asyncio
import logging
import time
from hashlib import sha1
from io import BytesIO
from os import urandom
from typing import Optional

import pyrogram
from pyrogram import raw
from pyrogram.connection import Connection
from pyrogram.crypto import aes, rsa, prime
from pyrogram.errors import SecurityCheckMismatch
from pyrogram.raw.core import TLObject, Long, Int
from .internals import MsgId

log = logging.getLogger(__name__)


class Auth:
    MAX_RETRIES = 5

    def __init__(
        self,
        client: "pyrogram.Client",
        dc_id: int,
        test_mode: bool
    ):
        self.dc_id = dc_id
        self.test_mode = test_mode
        self.ipv6 = client.ipv6
        self.alt_port = client.alt_port
        self.proxy = client.proxy
        self.connection_factory = client.connection_factory
        self.protocol_factory = client.protocol_factory

        self.connection: Optional[Connection] = None

    @staticmethod
    def pack(data: TLObject) -> bytes:
        return (
            bytes(8)
            + Long(MsgId())
            + Int(len(data.write()))
            + data.write()
        )

    @staticmethod
    def unpack(b: BytesIO):
        b.seek(20)  # Skip auth_key_id (8), message_id (8) and message_length (4)
        return TLObject.read(b)

    async def invoke(self, data: TLObject):
        data = self.pack(data)
        await self.connection.send(data)
        response = await self.connection.recv()

        # A 4-byte packet is a transport error code instead of an answer, e.g. -404 for rejected data
        if response is not None and len(response) == 4:
            raise ConnectionError(f"Server sent transport error: {Int.read(BytesIO(response))}")

        return self.unpack(BytesIO(response))

    async def create(self):
        """
        https://core.telegram.org/mtproto/auth_key
        https://core.telegram.org/mtproto/samples-auth_key
        """
        retries_left = self.MAX_RETRIES

        # The server may close the connection at any time, causing the auth key creation to fail.
        # If that happens, just try again up to MAX_RETRIES times.
        while True:
            self.connection = self.connection_factory(
                dc_id=self.dc_id,
                test_mode=self.test_mode,
                ipv6=self.ipv6,
                alt_port=self.alt_port,
                proxy=self.proxy,
                media=False,
                protocol_factory=self.protocol_factory
            )

            try:
                log.info("Start creating a new auth key on DC%s", self.dc_id)

                await self.connection.connect()

                # Step 1; Step 2
                nonce = int.from_bytes(urandom(16), "little", signed=True)
                log.debug("Send req_pq: %s", nonce)
                res_pq = await self.invoke(raw.functions.ReqPqMulti(nonce=nonce))
                log.debug("Got ResPq: %s", res_pq.server_nonce)
                log.debug("Server public key fingerprints: %s", res_pq.server_public_key_fingerprints)

                # Keys are tried in the order of rsa.server_public_keys, so the current main key is preferred:
                # the server rejects RSA_PAD data encrypted with the older keys it still lists.
                for i in rsa.server_public_keys:
                    if i in res_pq.server_public_key_fingerprints:
                        log.debug("Using fingerprint: %s", i)
                        public_key_fingerprint = i
                        break
                else:
                    raise Exception("Public key not found")

                # Step 3
                # pq is a product of two 32-bit primes; anything bigger would make the factorization run forever
                pq = int.from_bytes(res_pq.pq, "big")
                SecurityCheckMismatch.check(1 < pq < 2 ** 64, "1 < pq < 2 ** 64")
                log.debug("Start PQ factorization: %s", pq)
                start = time.time()
                g = prime.decompose(pq)
                p, q = sorted((g, pq // g))  # p < q
                SecurityCheckMismatch.check(1 < p and p * q == pq, "1 < p and p * q == pq")
                log.debug("Done PQ factorization (%ss): %s %s", round(time.time() - start, 3), p, q)

                # Step 4
                server_nonce = res_pq.server_nonce
                new_nonce = int.from_bytes(urandom(32), "little", signed=True)

                # https://core.telegram.org/mtproto/security_guidelines#checking-nonce-server-nonce-and-new-nonce-fields
                SecurityCheckMismatch.check(nonce == res_pq.nonce, "nonce == res_pq.nonce")

                # p_q_inner_data_dc names the DC the key is created for: 10000 is added for the test servers.
                # Auth always connects to a regular (non-media) DC, so the ID is never negative.
                data = raw.types.PQInnerDataDc(
                    pq=res_pq.pq,
                    p=p.to_bytes(4, "big"),
                    q=q.to_bytes(4, "big"),
                    nonce=nonce,
                    server_nonce=server_nonce,
                    new_nonce=new_nonce,
                    dc=self.dc_id + 10000 if self.test_mode else self.dc_id
                ).write()

                encrypted_data = rsa.pad_and_encrypt(data, public_key_fingerprint)

                log.debug("Done encrypt data with RSA_PAD")

                # Step 5
                log.debug("Send req_DH_params")
                server_dh_params = await self.invoke(
                    raw.functions.ReqDHParams(
                        nonce=nonce,
                        server_nonce=server_nonce,
                        p=p.to_bytes(4, "big"),
                        q=q.to_bytes(4, "big"),
                        public_key_fingerprint=public_key_fingerprint,
                        encrypted_data=encrypted_data
                    )
                )

                SecurityCheckMismatch.check(
                    isinstance(server_dh_params, raw.types.ServerDHParamsOk),
                    "isinstance(server_dh_params, raw.types.ServerDHParamsOk)"
                )
                SecurityCheckMismatch.check(nonce == server_dh_params.nonce, "nonce == server_dh_params.nonce")
                SecurityCheckMismatch.check(
                    server_nonce == server_dh_params.server_nonce,
                    "server_nonce == server_dh_params.server_nonce"
                )

                encrypted_answer = server_dh_params.encrypted_answer

                server_nonce = server_nonce.to_bytes(16, "little", signed=True)
                new_nonce = new_nonce.to_bytes(32, "little", signed=True)

                tmp_aes_key = (
                    sha1(new_nonce + server_nonce).digest()
                    + sha1(server_nonce + new_nonce).digest()[:12]
                )

                tmp_aes_iv = (
                    sha1(server_nonce + new_nonce).digest()[12:]
                    + sha1(new_nonce + new_nonce).digest() + new_nonce[:4]
                )

                server_nonce = int.from_bytes(server_nonce, "little", signed=True)

                answer_with_hash = aes.ige256_decrypt(encrypted_answer, tmp_aes_key, tmp_aes_iv)
                answer = answer_with_hash[20:]

                server_dh_inner_data = TLObject.read(BytesIO(answer))

                log.debug("Done decrypting answer")

                #######################
                # Security checks, all done before anything is computed from or sent based on the answer
                #######################

                # https://core.telegram.org/mtproto/security_guidelines#checking-sha1-hash-values
                answer = server_dh_inner_data.write()  # Call .write() to remove padding
                SecurityCheckMismatch.check(
                    answer_with_hash[:20] == sha1(answer).digest(),
                    "answer_with_hash[:20] == sha1(answer).digest()"
                )
                log.debug("SHA1 hash values check: OK")

                SecurityCheckMismatch.check(
                    isinstance(server_dh_inner_data, raw.types.ServerDHInnerData),
                    "isinstance(server_dh_inner_data, raw.types.ServerDHInnerData)"
                )
                SecurityCheckMismatch.check(nonce == server_dh_inner_data.nonce, "nonce == server_dh_inner_data.nonce")
                SecurityCheckMismatch.check(
                    server_nonce == server_dh_inner_data.server_nonce,
                    "server_nonce == server_dh_inner_data.server_nonce"
                )

                dh_prime = int.from_bytes(server_dh_inner_data.dh_prime, "big")
                SecurityCheckMismatch.check(dh_prime == prime.CURRENT_DH_PRIME, "dh_prime == prime.CURRENT_DH_PRIME")
                log.debug("DH parameters check: OK")

                # https://core.telegram.org/mtproto/security_guidelines#g-a-and-g-b-validation
                g = server_dh_inner_data.g
                g_a = int.from_bytes(server_dh_inner_data.g_a, "big")
                SecurityCheckMismatch.check(1 < g < dh_prime - 1, "1 < g < dh_prime - 1")
                SecurityCheckMismatch.check(1 < g_a < dh_prime - 1, "1 < g_a < dh_prime - 1")
                SecurityCheckMismatch.check(
                    2 ** (2048 - 64) < g_a < dh_prime - 2 ** (2048 - 64),
                    "2 ** (2048 - 64) < g_a < dh_prime - 2 ** (2048 - 64)"
                )

                delta_time = server_dh_inner_data.server_time - time.time()

                log.debug("Delta time: %s", round(delta_time, 3))

                # Step 6
                b = int.from_bytes(urandom(256), "big")
                g_b = pow(g, b, dh_prime)

                SecurityCheckMismatch.check(1 < g_b < dh_prime - 1, "1 < g_b < dh_prime - 1")
                SecurityCheckMismatch.check(
                    2 ** (2048 - 64) < g_b < dh_prime - 2 ** (2048 - 64),
                    "2 ** (2048 - 64) < g_b < dh_prime - 2 ** (2048 - 64)"
                )
                log.debug("g_a and g_b validation: OK")

                retry_id = 0

                data = raw.types.ClientDHInnerData(
                    nonce=nonce,
                    server_nonce=server_nonce,
                    retry_id=retry_id,
                    g_b=g_b.to_bytes(256, "big")
                ).write()

                sha = sha1(data).digest()
                padding = urandom(- (len(data) + len(sha)) % 16)
                data_with_hash = sha + data + padding
                encrypted_data = aes.ige256_encrypt(data_with_hash, tmp_aes_key, tmp_aes_iv)

                log.debug("Send set_client_DH_params")
                set_client_dh_params_answer = await self.invoke(
                    raw.functions.SetClientDHParams(
                        nonce=nonce,
                        server_nonce=server_nonce,
                        encrypted_data=encrypted_data
                    )
                )

                # Step 7; Step 8
                auth_key = pow(g_a, b, dh_prime).to_bytes(256, "big")

                # The server must confirm the key: dh_gen_retry and dh_gen_fail mean the key can't be used
                SecurityCheckMismatch.check(
                    isinstance(set_client_dh_params_answer, raw.types.DhGenOk),
                    "isinstance(set_client_dh_params_answer, raw.types.DhGenOk)"
                )
                SecurityCheckMismatch.check(
                    nonce == set_client_dh_params_answer.nonce,
                    "nonce == set_client_dh_params_answer.nonce"
                )
                SecurityCheckMismatch.check(
                    server_nonce == set_client_dh_params_answer.server_nonce,
                    "server_nonce == set_client_dh_params_answer.server_nonce"
                )

                # https://core.telegram.org/mtproto/auth_key#dh-key-exchange-complete
                # new_nonce_hash1 = lower 128 bits of SHA1(new_nonce + 1 + auth_key_aux_hash)
                auth_key_aux_hash = sha1(auth_key).digest()[:8]
                new_nonce_hash1 = int.from_bytes(
                    sha1(new_nonce + b"\x01" + auth_key_aux_hash).digest()[4:20], "little", signed=True
                )
                SecurityCheckMismatch.check(
                    new_nonce_hash1 == set_client_dh_params_answer.new_nonce_hash1,
                    "new_nonce_hash1 == set_client_dh_params_answer.new_nonce_hash1"
                )

                server_nonce = server_nonce.to_bytes(16, "little", signed=True)
                log.debug("Nonce fields check: OK")

                # Step 9
                server_salt = aes.xor(new_nonce[:8], server_nonce[:8])

                log.debug("Server salt: %s", int.from_bytes(server_salt, "little"))

                log.info("Done auth key exchange: %s", set_client_dh_params_answer.__class__.__name__)
            except Exception as e:
                log.info("Retrying due to %s: %s", type(e).__name__, e)

                if retries_left:
                    retries_left -= 1
                else:
                    raise e

                await asyncio.sleep(1)
                continue
            else:
                return auth_key
            finally:
                await self.connection.close()
