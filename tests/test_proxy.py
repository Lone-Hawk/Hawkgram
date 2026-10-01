#  Hawkgram - Telegram MTProto API Client Library for Python
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

"""Connections through SOCKS4, SOCKS5 and HTTP proxies, using small local proxy servers and an echo server."""

import asyncio
import base64
import ipaddress
import socket
import struct

import pytest
import pytest_asyncio

from pyrogram.connection.transport.tcp.tcp import TCP


async def pipe(reader, writer):
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, OSError):
        pass
    finally:
        writer.close()


class LocalProxy:
    """A minimal proxy server supporting one protocol, recording the destinations it was asked for."""

    def __init__(self, scheme, username=None, password=None):
        self.scheme = scheme
        self.username = username
        self.password = password
        self.destinations = []
        self.server = None

    async def start(self):
        self.server = await asyncio.start_server(self.handle, "127.0.0.1", 0)
        return self.server.sockets[0].getsockname()[1]

    async def stop(self):
        self.server.close()
        await self.server.wait_closed()

    async def handle(self, reader, writer):
        try:
            destination = await getattr(self, f"handshake_{self.scheme}")(reader, writer)
        except (ConnectionError, asyncio.IncompleteReadError, ValueError):
            writer.close()
            return

        if destination is None:
            writer.close()
            return

        self.destinations.append(destination)
        target_reader, target_writer = await asyncio.open_connection(*destination)
        await asyncio.gather(pipe(reader, target_writer), pipe(target_reader, writer))

    async def handshake_socks5(self, reader, writer):
        version, n_methods = await reader.readexactly(2)
        methods = await reader.readexactly(n_methods)
        assert version == 5

        if self.username:
            if 2 not in methods:
                writer.write(b"\x05\xff")
                return None
            writer.write(b"\x05\x02")
            _, user_length = await reader.readexactly(2)
            username = await reader.readexactly(user_length)
            password = await reader.readexactly((await reader.readexactly(1))[0])
            if (username.decode(), password.decode()) != (self.username, self.password):
                writer.write(b"\x01\x01")
                return None
            writer.write(b"\x01\x00")
        else:
            writer.write(b"\x05\x00")

        _, command, _, address_type = await reader.readexactly(4)
        assert command == 1
        if address_type == 1:
            host = socket.inet_ntoa(await reader.readexactly(4))
        elif address_type == 3:
            host = (await reader.readexactly((await reader.readexactly(1))[0])).decode()
        else:
            host = str(ipaddress.IPv6Address(await reader.readexactly(16)))
        port = struct.unpack(">H", await reader.readexactly(2))[0]

        writer.write(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + b"\x00\x00")
        return host, port

    async def handshake_socks4(self, reader, writer):
        version, command = await reader.readexactly(2)
        assert (version, command) == (4, 1)
        port = struct.unpack(">H", await reader.readexactly(2))[0]
        host = socket.inet_ntoa(await reader.readexactly(4))
        await reader.readuntil(b"\x00")  # user id

        writer.write(b"\x00\x5a" + b"\x00" * 6)
        return host, port

    async def handshake_http(self, reader, writer):
        request = (await reader.readuntil(b"\r\n\r\n")).decode()
        method, target, _ = request.split("\r\n")[0].split(" ")
        assert method == "CONNECT"

        if self.username:
            expected = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            if f"Proxy-Authorization: Basic {expected}".lower() not in request.lower():
                writer.write(b"HTTP/1.1 407 Proxy Authentication Required\r\n\r\n")
                return None

        writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
        host, port = target.rsplit(":", 1)
        return host, int(port)


@pytest_asyncio.fixture
async def echo_port():
    async def echo(reader, writer):
        await pipe(reader, writer)

    server = await asyncio.start_server(echo, "127.0.0.1", 0)
    yield server.sockets[0].getsockname()[1]
    server.close()
    await server.wait_closed()


async def exchange_through(proxy_server, proxy_config, echo_port):
    proxy_port = await proxy_server.start()
    tcp = TCP(ipv6=False, proxy={"hostname": "127.0.0.1", "port": proxy_port, **proxy_config})

    try:
        await tcp.connect(("127.0.0.1", echo_port))
        await tcp.send(b"hello telegram")
        return await tcp.recv(len(b"hello telegram"))
    finally:
        await tcp.close()
        await proxy_server.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("scheme, credentials", [
    ("socks5", {}),
    ("socks5", {"username": "user", "password": "secret"}),
    ("socks4", {}),
    ("http", {}),
    ("http", {"username": "user", "password": "secret"}),
])
async def test_connects_through_proxy(echo_port, scheme, credentials):
    proxy = LocalProxy(scheme, **credentials)

    received = await exchange_through(proxy, {"scheme": scheme, **credentials}, echo_port)

    assert received == b"hello telegram"
    assert proxy.destinations == [("127.0.0.1", echo_port)]


@pytest.mark.asyncio
@pytest.mark.parametrize("scheme", ["socks5", "http"])
async def test_wrong_proxy_password_fails(echo_port, scheme):
    proxy = LocalProxy(scheme, username="user", password="secret")

    with pytest.raises(Exception):
        await exchange_through(proxy, {"scheme": scheme, "username": "user", "password": "wrong"}, echo_port)

    assert proxy.destinations == []


@pytest.mark.asyncio
async def test_unknown_proxy_scheme_is_rejected():
    tcp = TCP(ipv6=False, proxy={"scheme": "ftp", "hostname": "127.0.0.1", "port": 1})

    with pytest.raises(ValueError):
        await tcp.connect(("127.0.0.1", 1))
