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
import os
import stat
import threading
from concurrent.futures import Executor
from typing import BinaryIO, Optional

# Not available on Windows
HAS_POSITIONAL_IO = hasattr(os, "pread") and hasattr(os, "pwrite")


class PartFile:
    """Read and write parts of a file at explicit offsets, in a thread instead of on the event loop.

    Regular files use ``os.pread`` / ``os.pwrite`` where the platform has them: they don't move the file position, so
    several tasks can read or write parts of the same file at once. Other file objects (``BytesIO``, files on Windows,
    pipes, objects without a file descriptor) seek and then read or write, one call at a time.

    A file object whose descriptor is used directly should have no buffered writes pending: call ``flush()`` (or
    ``seek()``, which flushes) on it first.

    Parameters:
        file (``BinaryIO``):
            The binary file object.

        executor (``Executor``, *optional*):
            The executor the calls run in. Defaults to the event loop's default executor.
    """

    def __init__(self, file: BinaryIO, executor: Optional[Executor] = None):
        self.file = file
        self.executor = executor
        self.fd = self._positional_fd(file)
        self.lock = threading.Lock()
        self.pending = set()

    @staticmethod
    def _positional_fd(file: BinaryIO) -> Optional[int]:
        if not HAS_POSITIONAL_IO:
            return None

        try:
            fd = file.fileno()
        except (AttributeError, OSError, ValueError):  # io.UnsupportedOperation is both OSError and ValueError
            return None

        try:
            is_regular = stat.S_ISREG(os.fstat(fd).st_mode)
        except OSError:
            return None

        return fd if is_regular else None

    def read_sync(self, offset: int, size: int) -> bytes:
        """Read up to *size* bytes at *offset*, fewer only at the end of the file."""
        if self.fd is None:
            with self.lock:
                self.file.seek(offset)
                return self.file.read(size)

        parts = []

        while size > 0:
            data = os.pread(self.fd, size, offset)

            if not data:
                break

            parts.append(data)
            offset += len(data)
            size -= len(data)

        return parts[0] if len(parts) == 1 else b"".join(parts)

    def write_sync(self, offset: int, data: bytes) -> None:
        """Write all of *data* at *offset*."""
        if self.fd is None:
            with self.lock:
                self.file.seek(offset)
                self.file.write(data)
            return

        view = memoryview(data)

        while view:
            written = os.pwrite(self.fd, view, offset)
            view = view[written:]
            offset += written

    async def _run(self, func, *args):
        future = asyncio.get_running_loop().run_in_executor(self.executor, func, *args)
        self.pending.add(future)
        future.add_done_callback(self.pending.discard)

        # A cancelled caller can't stop the thread: the call goes on and wait() waits for it
        return await asyncio.shield(future)

    async def read(self, offset: int, size: int) -> bytes:
        return await self._run(self.read_sync, offset, size)

    async def write(self, offset: int, data: bytes) -> None:
        await self._run(self.write_sync, offset, data)

    async def wait(self) -> None:
        """Wait for the reads and writes still running in a thread, e.g. after a cancelled transfer.

        Call it before closing the file: a descriptor closed while a thread still uses it can be given to another
        file that is opened meanwhile, and the thread would then read or write that file instead.
        """
        # Unlike gather(), wait() doesn't cancel the calls when the waiting task is cancelled
        if self.pending:
            await asyncio.wait(set(self.pending))


__all__ = ["HAS_POSITIONAL_IO", "PartFile"]
