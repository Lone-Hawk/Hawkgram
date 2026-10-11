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

"""Media sessions: one per DC, kept and shared by downloads, uploads and inline message edits"""

import asyncio
from io import BytesIO
from types import SimpleNamespace

import pytest
import pytest_asyncio

import pyrogram
from pyrogram import raw
from pyrogram.errors import AuthBytesInvalid, FilePartInvalid
from pyrogram.file_id import FileId, FileType
from pyrogram.methods.messages.inline_session import get_session

T = raw.types

OWN_DC = 2
OTHER_DC = 4


class FakeDcSession:
    """A media session to one DC: imports authorizations, serves file parts and accepts uploaded parts"""

    def __init__(self, client, dc_id, auth_key, test_mode, is_media=False, is_cdn=False, import_errors=0,
                 setup=None):
        self.dc_id = dc_id
        self.auth_key = auth_key
        self.import_errors = import_errors
        self.setup = setup
        self.requests = []
        self.started = self.stopped = False

    async def start(self):
        await asyncio.sleep(0)
        self.started = True

    async def stop(self):
        self.stopped = True

    async def invoke(self, query, *args, **kwargs):
        self.requests.append(query)

        if isinstance(query, raw.functions.auth.ImportAuthorization):
            if self.import_errors:
                self.import_errors -= 1
                raise AuthBytesInvalid()
            return T.auth.Authorization(user=T.User(id=1))

        if isinstance(query, raw.functions.upload.GetFile):
            return T.upload.File(type=T.storage.FileUnknown(), mtime=0, bytes=b"data")

        if isinstance(query, (raw.functions.upload.SaveFilePart, raw.functions.upload.SaveBigFilePart)):
            # Parts are sent concurrently by several workers
            await asyncio.sleep(0)

            if self.setup is not None and query.file_part == self.setup.fail_part:
                raise FilePartInvalid()

        return True


class Setup:
    """A client whose Session(), Auth().create() and ExportAuthorization are counted"""

    def __init__(self, client, monkeypatch, import_errors=0):
        self.client = client
        self.sessions = []
        self.auth_keys_created = 0
        self.exports = 0
        self.import_errors = import_errors
        self.fail_part = None

        def new_session(*args, **kwargs):
            session = FakeDcSession(*args, import_errors=self.import_errors, setup=self, **kwargs)
            self.sessions.append(session)
            return session

        setup = self

        class FakeAuth:
            def __init__(self, *args):
                pass

            async def create(self):
                setup.auth_keys_created += 1
                await asyncio.sleep(0)
                return bytes(256)

        async def invoke(query, *args, **kwargs):
            assert isinstance(query, raw.functions.auth.ExportAuthorization)
            self.exports += 1
            return T.auth.ExportedAuthorization(id=1, bytes=b"auth")

        monkeypatch.setattr("pyrogram.client.Session", new_session)
        monkeypatch.setattr("pyrogram.client.Auth", FakeAuth)
        client.invoke = invoke


@pytest_asyncio.fixture
async def setup(tmp_path, monkeypatch):
    client = pyrogram.Client("media", api_id=1, api_hash="0" * 32, in_memory=True, workdir=str(tmp_path))
    await client.storage.open()
    await client.storage.auth_key(b"k" * 256)

    return Setup(client, monkeypatch)


def file_id(dc_id):
    return FileId(file_type=FileType.DOCUMENT, dc_id=dc_id, media_id=1, access_hash=2)


async def download(client, dc_id):
    return [chunk async for chunk in client.get_file(file_id(dc_id), 4)]


@pytest.mark.asyncio
async def test_downloads_from_another_dc_share_one_session(setup):
    # Every download used to create a session, an auth key and an imported authorization of its own
    for _ in range(3):
        assert await download(setup.client, OTHER_DC) == [b"data"]

    (session,) = setup.sessions
    assert session.dc_id == OTHER_DC and session.started and not session.stopped
    assert setup.auth_keys_created == 1
    assert setup.exports == 1
    assert sum(isinstance(r, raw.functions.auth.ImportAuthorization) for r in session.requests) == 1
    assert setup.client.media_sessions == {OTHER_DC: session}


@pytest.mark.asyncio
async def test_downloads_from_the_own_dc_use_the_stored_auth_key(setup):
    await download(setup.client, OWN_DC)
    await download(setup.client, OWN_DC)

    (session,) = setup.sessions
    assert session.auth_key == b"k" * 256
    assert setup.auth_keys_created == 0 and setup.exports == 0


@pytest.mark.asyncio
async def test_uploads_share_the_own_dc_session(setup):
    setup.client.me = SimpleNamespace(is_premium=False)

    for _ in range(2):
        uploaded = await setup.client.save_file(BytesIO(b"x" * 1000))
        assert isinstance(uploaded, T.InputFile)

    (session,) = setup.sessions
    assert session.dc_id == OWN_DC and not session.stopped
    assert sum(isinstance(r, raw.functions.upload.SaveFilePart) for r in session.requests) == 2


@pytest.mark.asyncio
async def test_concurrent_transfers_create_one_session(setup):
    await asyncio.gather(*(download(setup.client, OTHER_DC) for _ in range(5)))

    assert len(setup.sessions) == 1
    assert setup.auth_keys_created == 1


@pytest.mark.asyncio
async def test_inline_edits_and_downloads_share_sessions(setup):
    session = await get_session(setup.client, OTHER_DC)
    await download(setup.client, OTHER_DC)

    assert setup.sessions == [session]
    # Inline messages of the own DC still go through the main session
    assert await get_session(setup.client, OWN_DC) is setup.client


@pytest.mark.asyncio
async def test_session_whose_authorization_failed_is_not_kept(setup):
    setup.import_errors = 3

    with pytest.raises(AuthBytesInvalid):
        await get_session(setup.client, OTHER_DC)

    # The failed session used to stay cached, so every later inline edit on that DC failed
    (failed,) = setup.sessions
    assert failed.stopped
    assert setup.client.media_sessions == {}

    setup.import_errors = 0
    session = await get_session(setup.client, OTHER_DC)

    assert session is not failed and session.started
    assert setup.client.media_sessions == {OTHER_DC: session}


@pytest.mark.asyncio
async def test_authorization_is_retried(setup):
    setup.import_errors = 2

    session = await get_session(setup.client, OTHER_DC)

    assert setup.exports == 3
    assert setup.client.media_sessions == {OTHER_DC: session}



# ---------------------------------------------------------------------------------------------------------------
# Uploads fail when a part fails
# ---------------------------------------------------------------------------------------------------------------

def uploaded_parts(session):
    return sorted(r.file_part for r in session.requests if hasattr(r, "file_part"))


@pytest.mark.asyncio
@pytest.mark.parametrize("size, fail_part", [
    (3 * 512 * 1024, 1),  # small file, one worker
    (11 * 1024 * 1024, 7),  # big file, four workers
], ids=["small", "big"])
async def test_upload_with_a_failed_part_raises(setup, tmp_path, size, fail_part):
    setup.client.me = SimpleNamespace(is_premium=False)
    setup.fail_part = fail_part
    path = tmp_path / "video.mp4"
    path.write_bytes(bytes(size))

    # The error used to be logged and the upload to return a file with a missing part (or None)
    with pytest.raises(FilePartInvalid):
        await setup.client.save_file(str(path))

    # The file opened from the path is closed: it can be deleted, also on Windows
    path.unlink()


@pytest.mark.asyncio
async def test_failed_missing_part_upload_raises(setup):
    setup.client.me = SimpleNamespace(is_premium=False)
    setup.fail_part = 2

    with pytest.raises(FilePartInvalid):
        await setup.client.save_file(BytesIO(bytes(3 * 512 * 1024)), file_id=123, file_part=2)


@pytest.mark.asyncio
async def test_missing_part_upload_sends_only_that_part(setup):
    setup.client.me = SimpleNamespace(is_premium=False)

    assert await setup.client.save_file(BytesIO(bytes(3 * 512 * 1024)), file_id=123, file_part=2) is None

    (session,) = setup.sessions
    assert uploaded_parts(session) == [2]


@pytest.mark.asyncio
async def test_big_upload_sends_every_part(setup):
    setup.client.me = SimpleNamespace(is_premium=False)

    uploaded = await setup.client.save_file(BytesIO(bytes(11 * 1024 * 1024)))

    assert isinstance(uploaded, T.InputFileBig) and uploaded.parts == 22
    (session,) = setup.sessions
    assert uploaded_parts(session) == list(range(22))
