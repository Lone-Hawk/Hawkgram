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
import os
import re
from datetime import datetime
from importlib import import_module
from typing import Type, Union

from pyrogram import __version__, raw
from pyrogram.raw.core import TLObject
from .exceptions.all import exceptions

log = logging.getLogger(__name__)

UNKNOWN_ERRORS_FILE = "unknown_errors.txt"
# When the file reaches this size it is moved to unknown_errors.txt.1, replacing the previous one,
# so the two files never take more than about twice this much space
UNKNOWN_ERRORS_MAX_SIZE = 1024 * 1024


def log_unknown_error(value, rpc_name: str):
    try:
        try:
            if os.path.getsize(UNKNOWN_ERRORS_FILE) >= UNKNOWN_ERRORS_MAX_SIZE:
                os.replace(UNKNOWN_ERRORS_FILE, UNKNOWN_ERRORS_FILE + ".1")
        except FileNotFoundError:
            pass

        with open(UNKNOWN_ERRORS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()}\t{value}\t{rpc_name}\n")
    except OSError as e:
        # Failing to record the error must not replace the error itself
        log.debug("Unable to write to %s: %s", UNKNOWN_ERRORS_FILE, e)


class RPCError(Exception):
    ID = None
    CODE = None
    NAME = None
    MESSAGE = "{value}"

    def __init__(
        self,
        value: Union[int, str, raw.types.RpcError] = None,
        rpc_name: str = None,
        is_unknown: bool = False,
        is_signed: bool = False
    ):
        super().__init__("Telegram says: [{}{} {}] {} Hawkgram {} thinks: {}".format(
            "-" if is_signed else "",
            self.CODE,
            self.ID or self.NAME,
            f'(caused by "{rpc_name}")' if rpc_name else "",
            __version__,
            self.MESSAGE.format(value=value),
        ))

        try:
            self.value = int(value)
        except (ValueError, TypeError):
            self.value = value

        if is_unknown:
            log_unknown_error(value, rpc_name)

    @staticmethod
    def raise_it(rpc_error: "raw.types.RpcError", rpc_type: Type[TLObject]):
        error_code = rpc_error.error_code
        is_signed = error_code < 0
        error_message = rpc_error.error_message
        rpc_name = ".".join(rpc_type.QUALNAME.split(".")[1:])

        if is_signed:
            error_code = -error_code

        if error_code not in exceptions:
            raise UnknownError(
                value=f"[{error_code} {error_message}]",
                rpc_name=rpc_name,
                is_unknown=True,
                is_signed=is_signed
            )

        error_id = re.sub(r"_\d+", "_X", error_message)

        if error_id not in exceptions[error_code]:
            raise getattr(
                import_module("pyrogram.errors"),
                exceptions[error_code]["_"]
            )(value=f"[{error_code} {error_message}]",
              rpc_name=rpc_name,
              is_unknown=True,
              is_signed=is_signed)

        value = re.search(r"_(\d+)", error_message)
        value = value.group(1) if value is not None else value

        raise getattr(
            import_module("pyrogram.errors"),
            exceptions[error_code][error_id]
        )(value=value,
          rpc_name=rpc_name,
          is_unknown=False,
          is_signed=is_signed)


class UnknownError(RPCError):
    CODE = 520
    """:obj:`int`: Error code"""
    NAME = "Unknown error"
