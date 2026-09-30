#  Hawkgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2022-present Mayuri-Chan <https://github.com/Mayuri-Chan>
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

from pyrogram import raw
from ..object import Object


class InputReplyToMonoforum(Object):
    """Contains information about a target replied monoforum.


    Parameters:
        monoforum_peer (:obj:`~pyrogram.raw.base.InputPeer`):
            An InputPeer.
    """

    def __init__(
        self, *,
        monoforum_peer: "raw.base.InputPeer"
    ):
        super().__init__()

        self.monoforum_peer = monoforum_peer

    def write(self):
        return raw.types.InputReplyToMonoForum(
            monoforum_peer_id=self.monoforum_peer
        ).write()
