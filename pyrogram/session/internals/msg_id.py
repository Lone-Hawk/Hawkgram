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
import time

log = logging.getLogger(__name__)


class MsgId:
    last_time = 0
    offset = 0
    # Seconds to add to the local clock to get Telegram's time. msg_ids must carry the server's time (within -300 and
    # +30 seconds), so a client whose clock is off has to correct it: see Session.handle_packet
    server_time_offset = 0

    def __new__(cls) -> int:
        now = int(time.time() + cls.server_time_offset)
        cls.offset = (cls.offset + 4) if now == cls.last_time else 0
        msg_id = (now * 2 ** 32) + cls.offset
        cls.last_time = now

        return msg_id

    @classmethod
    def set_server_time(cls, server_msg_id: int):
        """Synchronize with the server's clock, given a msg_id sent by the server (its time is in the upper 32 bits)"""
        cls.server_time_offset = server_msg_id / 2 ** 32 - time.time()

        log.warning(
            "The system clock is %.0f seconds off Telegram's time: using Telegram's time instead",
            -cls.server_time_offset
        )
