# oz_externship_be/apps/chat/routing.py
from typing import List

from django.urls import URLPattern, path

from . import consumers

websocket_urlpatterns: List[URLPattern] = [
    # ws/chat/<스터디그룹UUID>/ 경로로 들어오는 WebSocket 요청을 ChatConsumer가 처리하도록 설정
    path(
        "ws/chat/<uuid:study_group_uuid>/",
        consumers.ChatConsumer.as_asgi(),  # type: ignore
        name="ws_chat_room",
    ),
]
