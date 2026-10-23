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

"""Uploads and downloads: file I/O in threads and progress reporting"""

import asyncio
import io
import os
import threading
from types import SimpleNamespace

import pytest
import pytest_asyncio

import pyrogram
from pyrogram import file_io, raw
from pyrogram.file_id import FileId, FileType
from pyrogram.file_io import PartFile

T = raw.types

PART_SIZE = 512 * 1024
CHUNK_SIZE = 1024 * 1024

needs_positional_io = pytest.mark.skipif(not file_io.HAS_POSITIONAL_IO, reason="no os.pread / os.pwrite here")


class FakeMediaSession:
    """Accepts uploaded parts and serves file chunks, remembering the thread every call ran in"""

    def __init__(self, data: bytes = b"", delays=None):
        self.data = data
        self.delays = delays or {}
        self.parts = {}
        self.order = []

    async def invoke(self, query, *args, **kwargs):
        if isinstance(query, raw.functions.upload.GetFile):
            return T.upload.File(
                type=T.storage.FileUnknown(), mtime=0, bytes=self.data[query.offset:query.offset + query.limit]
            )

        # Parts are sent concurrently by several workers: a delay makes them finish out of order
        await asyncio.sleep(self.delays.get(query.file_part, 0))
        self.parts[query.file_part] = query.bytes
        self.order.append(query.file_part)

        return True

    def uploaded(self) -> bytes:
        return b"".join(self.parts[i] for i in sorted(self.parts))


@pytest_asyncio.fixture
async def client(tmp_path):
    client = pyrogram.Client("transfers", api_id=1, api_hash="0" * 32, in_memory=True, workdir=str(tmp_path))
    await client.storage.open()
    await client.storage.dc_id(2)
    client.me = SimpleNamespace(is_premium=False)

    return client


def use_session(client, session):
    async def get_media_session(dc_id, is_cdn=False):
        return session

    client._get_media_session = get_media_session


class ThreadRecordingIO(io.BytesIO):
    """A file object without a descriptor that remembers which threads read and wrote it"""

    def __init__(self, *args):
        super().__init__(*args)
        self.threads = set()

    def read(self, *args):
        self.threads.add(threading.get_ident())
        return super().read(*args)

    def write(self, data):
        self.threads.add(threading.get_ident())
        return super().write(data)


# ---------------------------------------------------------------------------------------------------------------
# PartFile
# ---------------------------------------------------------------------------------------------------------------

@pytest.fixture(params=["positional", "seek"])
def part_file_mode(request, monkeypatch):
    if request.param == "positional":
        if not file_io.HAS_POSITIONAL_IO:
            pytest.skip("no os.pread / os.pwrite here")
    else:
        monkeypatch.setattr(file_io, "HAS_POSITIONAL_IO", False)

    return request.param


@pytest.mark.asyncio
async def test_part_file_reads_parts_at_their_offsets(tmp_path, part_file_mode):
    data = os.urandom(3 * PART_SIZE + 100)
    path = tmp_path / "file.bin"
    path.write_bytes(data)

    with open(path, "rb") as f:
        part_file = PartFile(f)
        assert (part_file.fd is not None) == (part_file_mode == "positional")

        # Out of order, as parallel parts will be read
        assert await part_file.read(2 * PART_SIZE, PART_SIZE) == data[2 * PART_SIZE:3 * PART_SIZE]
        assert await part_file.read(0, PART_SIZE) == data[:PART_SIZE]
        assert await part_file.read(3 * PART_SIZE, PART_SIZE) == data[3 * PART_SIZE:]
        assert await part_file.read(4 * PART_SIZE, PART_SIZE) == b""


@pytest.mark.asyncio
async def test_part_file_writes_parts_at_their_offsets(tmp_path, part_file_mode):
    parts = [os.urandom(PART_SIZE) for _ in range(3)] + [os.urandom(10)]
    path = tmp_path / "file.bin"

    with open(path, "xb") as f:
        part_file = PartFile(f)

        for i in (2, 0, 3, 1):
            await part_file.write(i * PART_SIZE, parts[i])

    assert path.read_bytes() == b"".join(parts)


@pytest.mark.asyncio
async def test_short_positional_reads_and_writes_are_continued(tmp_path, monkeypatch):
    # os.pread / os.pwrite may move fewer bytes than asked for; emulated so this also runs on Windows
    def pread(fd, size, offset):
        os.lseek(fd, offset, os.SEEK_SET)
        return os.read(fd, min(size, 1000))

    def pwrite(fd, data, offset):
        os.lseek(fd, offset, os.SEEK_SET)
        return os.write(fd, data[:1000])

    monkeypatch.setattr(file_io, "HAS_POSITIONAL_IO", True)
    monkeypatch.setattr(os, "pread", pread, raising=False)
    monkeypatch.setattr(os, "pwrite", pwrite, raising=False)
    data = os.urandom(PART_SIZE)
    path = tmp_path / "file.bin"

    with open(path, "w+b") as f:
        part_file = PartFile(f)
        assert part_file.fd is not None

        await part_file.write(0, data)
        assert await part_file.read(0, PART_SIZE + 10) == data
        assert await part_file.read(100, 5000) == data[100:5100]


def test_pipes_are_not_read_positionally(monkeypatch):
    monkeypatch.setattr(file_io, "HAS_POSITIONAL_IO", True)
    read_fd, write_fd = os.pipe()

    try:
        with os.fdopen(read_fd, "rb") as f:
            assert PartFile(f).fd is None
    finally:
        os.close(write_fd)


@needs_positional_io
@pytest.mark.asyncio
async def test_positional_reads_leave_the_file_position_alone(tmp_path):
    path = tmp_path / "file.bin"
    path.write_bytes(b"0123456789")

    with open(path, "rb") as f:
        f.seek(3)
        assert await PartFile(f).read(5, 2) == b"56"
        assert f.tell() == 3


@pytest.mark.asyncio
async def test_part_file_runs_in_a_thread_for_objects_without_a_descriptor():
    file = ThreadRecordingIO(b"abcdef")
    part_file = PartFile(file)

    assert part_file.fd is None
    assert await part_file.read(2, 3) == b"cde"
    await part_file.write(6, b"gh")

    assert file.getvalue() == b"abcdefgh"
    assert threading.get_ident() not in file.threads


@pytest.mark.asyncio
async def test_wait_waits_for_a_write_whose_caller_was_cancelled():
    started = threading.Event()
    release = threading.Event()

    class SlowIO(io.BytesIO):
        def write(self, data):
            started.set()
            release.wait(5)
            return super().write(data)

    file = SlowIO()
    part_file = PartFile(file)
    task = asyncio.create_task(part_file.write(0, b"data"))

    await asyncio.get_running_loop().run_in_executor(None, started.wait, 5)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    # The thread is still writing: closing the file now would hand its descriptor to the next file opened
    waiter = asyncio.create_task(part_file.wait())
    await asyncio.sleep(0.05)
    assert not waiter.done()

    release.set()
    await asyncio.wait_for(waiter, 5)
    assert file.getvalue() == b"data"


# ---------------------------------------------------------------------------------------------------------------
# File I/O of uploads and downloads
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("size", [3 * PART_SIZE + 7, 11 * 1024 * 1024 + 7], ids=["small", "big"])
async def test_upload_by_path_sends_the_whole_file(client, tmp_path, size):
    data = os.urandom(size)
    path = tmp_path / "video.mp4"
    path.write_bytes(data)
    session = FakeMediaSession()
    use_session(client, session)

    uploaded = await client.save_file(str(path))

    assert uploaded.parts == len(session.parts) == -(-size // PART_SIZE)
    assert session.uploaded() == data
    # The file opened from the path is closed: it can be deleted, also on Windows
    path.unlink()


@pytest.mark.asyncio
async def test_upload_reads_file_objects_in_a_thread(client):
    data = os.urandom(3 * PART_SIZE)
    file = ThreadRecordingIO(data)
    session = FakeMediaSession()
    use_session(client, session)

    await client.save_file(file)

    assert session.uploaded() == data
    assert file.threads and threading.get_ident() not in file.threads


@pytest.mark.asyncio
async def test_missing_part_upload_reads_only_that_part(client):
    data = os.urandom(3 * PART_SIZE)
    session = FakeMediaSession()
    use_session(client, session)

    assert await client.save_file(io.BytesIO(data), file_id=123, file_part=1) is None
    assert session.parts == {1: data[PART_SIZE:2 * PART_SIZE]}


def document_file_id():
    return FileId(file_type=FileType.DOCUMENT, dc_id=2, media_id=1, access_hash=2)


@pytest.mark.asyncio
async def test_download_to_disk_writes_every_chunk(client, tmp_path):
    data = os.urandom(2 * CHUNK_SIZE + 10)
    use_session(client, FakeMediaSession(data))
    directory = tmp_path / "downloads"

    result = await client.handle_download((document_file_id(), str(directory), "video.mp4", False, len(data), None, ()))

    assert result == str(directory / "video.mp4")
    assert (directory / "video.mp4").read_bytes() == data


@pytest.mark.asyncio
async def test_download_in_memory_writes_in_a_thread(client, tmp_path, monkeypatch):
    data = os.urandom(2 * CHUNK_SIZE + 10)
    use_session(client, FakeMediaSession(data))
    monkeypatch.setattr("pyrogram.client.BytesIO", ThreadRecordingIO)

    result = await client.handle_download((document_file_id(), str(tmp_path), "video.mp4", True, len(data), None, ()))

    assert result.getvalue() == data and result.name == "video.mp4"
    # Left at the end, as when the chunks were written on the event loop
    assert result.tell() == len(data)
    assert result.threads and threading.get_ident() not in result.threads


# ---------------------------------------------------------------------------------------------------------------
# Upload and download progress
# ---------------------------------------------------------------------------------------------------------------

BIG_SIZE = 11 * 1024 * 1024 + 7  # 23 parts, uploaded by four workers


class ProgressRecorder:
    def __init__(self, session=None):
        self.session = session
        self.calls = []

        # A coroutine function, not an object with an async __call__: only those are awaited
        async def callback(current, total, *args):
            confirmed = sum(len(p) for p in session.parts.values()) if session else None
            self.calls.append((current, total, args, confirmed))
            await asyncio.sleep(0)

        self.callback = callback

    @property
    def currents(self):
        return [c[0] for c in self.calls]


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [3 * PART_SIZE + 7, BIG_SIZE], ids=["small", "big"])
async def test_upload_progress_only_counts_confirmed_parts(client, size):
    # The first parts are confirmed last, so parts finish out of order
    session = FakeMediaSession(delays={0: 0.05, 1: 0.03})
    use_session(client, session)
    progress = ProgressRecorder(session)

    await client.save_file(io.BytesIO(os.urandom(size)), progress=progress.callback, progress_args=("arg",))

    parts = -(-size // PART_SIZE)
    assert len(progress.calls) == parts
    # Reported when the part was queued, progress ran ahead of what Telegram had and reached 100% too early
    assert all(current <= confirmed for current, _, _, confirmed in progress.calls)
    assert all(total == size and args == ("arg",) for _, total, args, _ in progress.calls)
    assert progress.currents == sorted(set(progress.currents))
    assert progress.currents[-1] == size


@pytest.mark.asyncio
async def test_upload_progress_calls_sync_callbacks_one_at_a_time(client):
    session = FakeMediaSession(delays={0: 0.05})
    use_session(client, session)
    calls = []
    running = []

    def progress(current, total):
        running.append(current)
        assert len(running) == 1, "callbacks overlapped"
        threading.Event().wait(0.001)
        calls.append((current, threading.get_ident()))
        running.pop()

    await client.save_file(io.BytesIO(os.urandom(BIG_SIZE)), progress=progress)

    currents = [c for c, _ in calls]
    assert len(calls) == 23 and currents == sorted(currents) and currents[-1] == BIG_SIZE
    assert threading.get_ident() not in {t for _, t in calls}


@pytest.mark.asyncio
async def test_stop_transmission_from_the_progress_callback_stops_the_upload(client):
    session = FakeMediaSession()
    use_session(client, session)

    async def progress(current, total):
        if current >= 2 * PART_SIZE:
            raise pyrogram.StopTransmission()

    with pytest.raises(pyrogram.StopTransmission):
        await client.save_file(io.BytesIO(os.urandom(BIG_SIZE)), progress=progress)

    assert len(session.parts) < 23


@pytest.mark.asyncio
async def test_missing_part_upload_reports_no_progress(client):
    use_session(client, FakeMediaSession())
    progress = ProgressRecorder()

    await client.save_file(io.BytesIO(os.urandom(3 * PART_SIZE)), file_id=123, file_part=1, progress=progress.callback)

    assert progress.calls == []


@pytest.mark.asyncio
async def test_upload_progress_interval_reports_the_first_and_the_last_part(client):
    use_session(client, FakeMediaSession())
    progress = ProgressRecorder()

    await client.save_file(io.BytesIO(os.urandom(BIG_SIZE)), progress=progress.callback, progress_interval=3600)

    assert progress.currents == [PART_SIZE, BIG_SIZE]


@pytest.mark.asyncio
async def test_upload_progress_interval_defaults_to_the_clients(client):
    use_session(client, FakeMediaSession())
    client.progress_interval = 3600
    throttled, every_part = ProgressRecorder(), ProgressRecorder()

    await client.save_file(io.BytesIO(os.urandom(BIG_SIZE)), progress=throttled.callback)
    await client.save_file(io.BytesIO(os.urandom(BIG_SIZE)), progress=every_part.callback, progress_interval=0)

    assert len(throttled.calls) == 2
    assert len(every_part.calls) == 23


@pytest.mark.asyncio
@pytest.mark.parametrize("interval, expected", [
    (None, [CHUNK_SIZE, 2 * CHUNK_SIZE, 2 * CHUNK_SIZE + 10]),
    (3600, [CHUNK_SIZE, 2 * CHUNK_SIZE + 10]),
])
async def test_download_progress_interval(client, tmp_path, interval, expected):
    data = os.urandom(2 * CHUNK_SIZE + 10)
    use_session(client, FakeMediaSession(data))
    client.progress_interval = interval
    progress = ProgressRecorder()

    packet = (document_file_id(), str(tmp_path), "video.mp4", False, len(data), progress.callback, ())
    await client.handle_download(packet)

    assert progress.currents == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("with_progress", [False, True], ids=["no-progress", "progress"])
async def test_download_of_media_without_a_size(client, tmp_path, with_progress):
    # Media built by hand (e.g. types.Document without file_size) have file_size=None: the last-chunk check compared
    # it with a number and raised TypeError for every download, so download_media returned None
    data = os.urandom(CHUNK_SIZE + 10)
    use_session(client, FakeMediaSession(data))
    progress = ProgressRecorder()

    packet = (document_file_id(), str(tmp_path), "video.mp4", False, None,
              progress.callback if with_progress else None, ())

    assert await client.handle_download(packet) == str(tmp_path / "video.mp4")
    assert (tmp_path / "video.mp4").read_bytes() == data

    if with_progress:
        # The size is unknown, so the bytes downloaded so far are reported, as for a size of 0
        assert progress.currents == [CHUNK_SIZE, 2 * CHUNK_SIZE]
        assert {c[1] for c in progress.calls} == {0}


def test_progress_throttle(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(pyrogram.utils.ProgressThrottle, "clock", staticmethod(lambda: now[0]))
    throttle = pyrogram.utils.ProgressThrottle(2)
    made = []

    for t in (0, 0.5, 1.9, 2.0, 2.1, 3.9, 4.5, 4.6):
        now[0] = 100 + t
        made.append(throttle())

    assert made == [True, False, False, True, False, False, True, False]
    # The last is always made
    assert throttle(is_last=True)
    assert all(pyrogram.utils.ProgressThrottle(None)() for _ in range(3))


@pytest.mark.parametrize("interval", [-1, float("nan")])
def test_invalid_progress_interval_is_refused(tmp_path, interval):
    with pytest.raises(ValueError):
        pyrogram.Client("transfers", api_id=1, api_hash="0" * 32, in_memory=True, progress_interval=interval)
