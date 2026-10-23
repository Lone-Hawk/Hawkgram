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

"""Upload and download speed of this Hawkgram checkout against real Telegram servers.

For each size, uploads a file of random bytes to a chat, downloads it back, checks it, reports MiB/s, the account's
home DC and the DC the file was stored on, then deletes the message. Not collected by pytest: it needs an account.

Settings come from environment variables:
    API_ID, API_HASH       from https://my.telegram.org
    BOT_TOKEN              a bot that may post in the chat, or
    SESSION_STRING         a user session string (used with --user, or when BOT_TOKEN isn't set)
    CHAT_ID                the chat to upload to: use a throwaway test chat

Run from the repository root:
    python tests/bench/transfer_bench.py --sizes 20,200 [--user] [--progress-interval 5]
"""

import argparse
import asyncio
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

# Benchmark this checkout, not an installed Hawkgram
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pyrogram  # noqa: E402
from pyrogram import Client  # noqa: E402
from pyrogram.crypto import aes  # noqa: E402,F401  (imports TgCrypto when installed)
from pyrogram.file_id import FileId  # noqa: E402

MIB = 1024 * 1024


def make_file(directory: Path, size_mib: int) -> Path:
    path = directory / f"bench-{size_mib}MiB.bin"

    with path.open("wb") as f:
        for _ in range(size_mib):
            f.write(os.urandom(MIB))

    return path


def same_content(a: Path, b: Path) -> bool:
    with a.open("rb") as fa, b.open("rb") as fb:
        while True:
            chunk_a, chunk_b = fa.read(MIB), fb.read(MIB)

            if chunk_a != chunk_b:
                return False

            if not chunk_a:
                return True


class ProgressCounter:
    """Counts progress callbacks and remembers when the last one (100%) came"""

    def __init__(self):
        self.calls = 0
        self.last = 0
        self.done_at = None

    async def __call__(self, current, total):
        self.calls += 1
        assert current >= self.last, f"progress went back from {self.last} to {current}"
        self.last = current

        if current == total:
            self.done_at = time.perf_counter()


async def bench(app: Client, chat_id: int, path: Path, workdir: Path, keep: bool) -> bool:
    size = await asyncio.to_thread(os.path.getsize, path)
    up, down = ProgressCounter(), ProgressCounter()

    start = time.perf_counter()
    # A bound method, so the client awaits it (an object with an async __call__ would be run in a thread)
    message = await app.send_document(
        chat_id, str(path), file_name=path.name, force_document=True, progress=up.__call__
    )
    upload_s = time.perf_counter() - start
    # How long after the 100% callback the message was sent: Telegram assembling the file and sending the message
    after_100 = (time.perf_counter() - up.done_at) if up.done_at else float("nan")

    file_dc = FileId.decode(message.document.file_id).dc_id

    start = time.perf_counter()
    downloaded = await app.download_media(
        message, file_name=str(workdir / f"down-{path.name}"), progress=down.__call__
    )
    download_s = time.perf_counter() - start

    ok = bool(downloaded) and await asyncio.to_thread(same_content, path, Path(downloaded))

    if ok:
        print(
            f"  {size / MIB:7.0f} MiB | upload {size / MIB / upload_s:7.2f} MiB/s ({upload_s:6.1f} s,"
            f" {up.calls} callbacks, sent {after_100:4.1f} s after 100%)"
            f" | download {size / MIB / download_s:7.2f} MiB/s ({download_s:6.1f} s, {down.calls} callbacks)"
            f" | file on DC{file_dc}"
        )
    else:
        print(f"  {path.name}: download failed or content mismatch")

    if downloaded:
        await asyncio.to_thread(os.remove, downloaded)

    if not keep:
        await message.delete()

    return ok


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sizes", default="20,200", help="comma-separated file sizes in MiB (default: 20,200)")
    parser.add_argument("--user", action="store_true", help="use SESSION_STRING instead of BOT_TOKEN")
    parser.add_argument(
        "--progress-interval", type=float, default=None,
        help="seconds between progress callbacks (default: one per part or chunk)"
    )
    parser.add_argument("--ipv6", action="store_true", help="connect to Telegram over IPv6")
    parser.add_argument("--keep", action="store_true", help="don't delete the uploaded messages")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    try:
        api_id = int(os.environ["API_ID"])
        api_hash = os.environ["API_HASH"]
        chat_id = int(os.environ["CHAT_ID"])

        if args.user or not os.environ.get("BOT_TOKEN"):
            credentials, kind = {"session_string": os.environ["SESSION_STRING"]}, "user"
        else:
            credentials, kind = {"bot_token": os.environ["BOT_TOKEN"]}, "bot"
    except (KeyError, ValueError) as e:
        print(f"Missing or invalid environment variable: {e}. See the docstring of {Path(__file__).name}.")
        return 1

    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]

    # Temporary files and an in-memory session: nothing is left behind
    with tempfile.TemporaryDirectory(prefix="hawkgram-bench-") as tmp:
        workdir = Path(tmp)
        files = [await asyncio.to_thread(make_file, workdir, size) for size in sizes]

        app = Client(
            "bench", api_id=api_id, api_hash=api_hash, in_memory=True, ipv6=args.ipv6,
            progress_interval=args.progress_interval, **credentials
        )

        async with app:
            me = await app.get_me()
            premium = " (Premium)" if getattr(me, "is_premium", False) else ""
            print(
                f"Hawkgram {pyrogram.__version__} | {kind}{premium}, home DC{await app.storage.dc_id()}"
                f" | progress interval {app.progress_interval}"
                f" | TgCrypto {'yes' if 'tgcrypto' in sys.modules else 'no'}"
            )

            results = [await bench(app, chat_id, path, workdir, args.keep) for path in files]

    return 0 if all(results) else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
