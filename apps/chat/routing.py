# oz_externship_be/apps/chat/routing.py
from typing import List

from django.urls import URLPattern, path

from . import consumers

websocket_urlpatterns: List[URLPattern] = [
    path(
        "ws/chat/rooms/<uuid:study_group_uuid>/",
        consumers.ChatConsumer.as_asgi(),  # type: ignore
        name="ws_chat_room",
    ),
]
