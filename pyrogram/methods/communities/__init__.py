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

from .approve_all_community_link_requests import ApproveAllCommunityLinkRequests
from .approve_community_link_request import ApproveCommunityLinkRequest
from .ban_community_member import BanCommunityMember
from .create_community import CreateCommunity
from .decline_all_community_link_requests import DeclineAllCommunityLinkRequests
from .decline_community_link_request import DeclineCommunityLinkRequest
from .get_community_link_requests import GetCommunityLinkRequests
from .get_community_member_chats import GetCommunityMemberChats
from .get_joined_communities import GetJoinedCommunities
from .remove_chat_from_community import RemoveChatFromCommunity
from .set_community_chat_hidden import SetCommunityChatHidden
from .set_community_collapsed import SetCommunityCollapsed
from .unban_community_member import UnbanCommunityMember


class Communities(
    ApproveAllCommunityLinkRequests,
    ApproveCommunityLinkRequest,
    BanCommunityMember,
    CreateCommunity,
    DeclineAllCommunityLinkRequests,
    DeclineCommunityLinkRequest,
    GetCommunityLinkRequests,
    GetCommunityMemberChats,
    GetJoinedCommunities,
    RemoveChatFromCommunity,
    SetCommunityChatHidden,
    SetCommunityCollapsed,
    UnbanCommunityMember,
):
    pass
