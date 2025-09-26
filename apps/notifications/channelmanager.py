from __future__ import annotations

from typing import Any

from django_eventstream.channelmanager import (  # type: ignore[import-untyped]
    DefaultChannelManager,
)


class NotificationChannelManager(DefaultChannelManager):  # type: ignore[misc]
    # 유저 별 채널 권한
    def permission_channel(self, user: Any, channel: str) -> bool:
        if not getattr(user, "is_authenticated", False):
            return False
        if channel.startswith("user-"):
            try:
                target_id = int(channel.split("-", 1)[1])
            except ValueError:
                return False
            return getattr(user, "id", None) == target_id
        return False
