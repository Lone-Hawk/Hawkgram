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

With --parallel N, N copies are uploaded at once and then downloaded at once, and the total throughput is reported
(the client is allowed N concurrent transmissions for that): what one client gets from Telegram with several
transfers at once, where a single transfer is often limited by the connection.

Settings come from environment variables:
    API_ID, API_HASH       from https://my.telegram.org
    BOT_TOKEN              a bot that may post in the chat, or
    SESSION_STRING         a user session string (used with --user, or when BOT_TOKEN isn't set)
    CHAT_ID                the chat to upload to: use a throwaway test chat

Run from the repository root:
    python tests/bench/transfer_bench.py --sizes 20,200 [--user] [--progress-interval 5]
                                         [--parallel 4]
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


async def upload(app: Client, chat_id: int, path: Path):
    """Upload one copy: returns the message, its progress and when it finished"""
    progress = ProgressCounter()
    # A bound method, so the client awaits it (an object with an async __call__ would be run in a thread)
    message = await app.send_document(
        chat_id, str(path), file_name=path.name, force_document=True, progress=progress.__call__
    )

    return message, progress, time.perf_counter()


async def download(app: Client, message, target: Path):
    """Download one copy: returns its path (None if it failed), its progress and when it finished"""
    progress = ProgressCounter()
    downloaded = await app.download_media(message, file_name=str(target), progress=progress.__call__)

    return downloaded, progress, time.perf_counter()


async def bench(app: Client, chat_id: int, path: Path, workdir: Path, keep: bool, parallel: int) -> bool:
    size = await asyncio.to_thread(os.path.getsize, path)
    mib = size / MIB

    upload_start = time.perf_counter()
    uploads = await asyncio.gather(*(upload(app, chat_id, path) for _ in range(parallel)), return_exceptions=True)
    upload_s = time.perf_counter() - upload_start
    messages = [u[0] for u in uploads if not isinstance(u, BaseException)]
    failed = [u for u in uploads if isinstance(u, BaseException)]

    downloads = []

    if not failed:
        download_start = time.perf_counter()
        downloads = await asyncio.gather(
            *(download(app, m, workdir / f"down-{i}-{path.name}") for i, m in enumerate(messages)),
            return_exceptions=True
        )
        download_s = time.perf_counter() - download_start
        failed = [d for d in downloads if isinstance(d, BaseException)]

    downloaded = [d[0] for d in downloads if not isinstance(d, BaseException)]
    ok = not failed and len(downloaded) == parallel

    for d in downloaded:
        ok = ok and d is not None and await asyncio.to_thread(same_content, path, Path(d))

    if not ok:
        reason = f"{type(failed[0]).__name__}: {failed[0]}" if failed else "download failed or content mismatch"
        print(f"  {path.name}{f' x{parallel}' if parallel > 1 else ''}: {reason}")
    elif parallel == 1:
        (message, up, uploaded_at), ((_, down, _),) = uploads[0], downloads
        # How long after the 100% callback the message was sent: Telegram assembling the file and sending the message
        after_100 = (uploaded_at - up.done_at) if up.done_at else float("nan")
        print(
            f"  {mib:7.0f} MiB | upload {mib / upload_s:7.2f} MiB/s ({upload_s:6.1f} s,"
            f" {up.calls} callbacks, sent {after_100:4.1f} s after 100%)"
            f" | download {mib / download_s:7.2f} MiB/s ({download_s:6.1f} s, {down.calls} callbacks)"
            f" | file on DC{FileId.decode(message.document.file_id).dc_id}"
        )
    else:
        # Total throughput over the time all copies took, and when the first copy was done (if far earlier than the
        # last, the transfers didn't share the connection evenly)
        first_upload_s = min(u[2] for u in uploads) - upload_start
        first_download_s = min(d[2] for d in downloads) - download_start
        dcs = sorted({FileId.decode(m.document.file_id).dc_id for m in messages})
        print(
            f"  {mib:7.0f} MiB x{parallel} | upload {parallel * mib / upload_s:7.2f} MiB/s total ({upload_s:6.1f} s,"
            f" first done after {first_upload_s:6.1f} s)"
            f" | download {parallel * mib / download_s:7.2f} MiB/s total ({download_s:6.1f} s,"
            f" first done after {first_download_s:6.1f} s)"
            f" | files on DC{'/DC'.join(map(str, dcs))}"
        )

    for d in downloaded:
        if d:
            await asyncio.to_thread(os.remove, d)

    if not keep:
        for message in messages:
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
    parser.add_argument(
        "--parallel", type=int, default=1,
        help="copies of each size uploaded at once, then downloaded at once (default: 1)"
    )
    args = parser.parse_args()

    if args.parallel < 1:
        parser.error("--parallel must be at least 1")

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
            progress_interval=args.progress_interval,
            # Uploads and downloads otherwise wait for each other: one transmission at a time by default
            max_concurrent_transmissions=args.parallel, **credentials
        )

        async with app:
            me = await app.get_me()
            premium = " (Premium)" if getattr(me, "is_premium", False) else ""
            print(
                f"Hawkgram {pyrogram.__version__} | {kind}{premium}, home DC{await app.storage.dc_id()}"
                f" | progress interval {app.progress_interval}"
                f" | parallel {args.parallel}"
                f" | TgCrypto {'yes' if 'tgcrypto' in sys.modules else 'no'}"
            )

            results = [await bench(app, chat_id, path, workdir, args.keep, args.parallel) for path in files]

    return 0 if all(results) else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
