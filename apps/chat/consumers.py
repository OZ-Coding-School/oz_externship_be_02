# oz_externship_be/apps/chat/consumers.py
import json
from typing import Any, Dict, Optional

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    """
    스터디 그룹 채팅을 위한 WebSocket Consumer의 기본 구조입니다.
    """

    async def connect(self) -> None:
        """
        클라이언트가 WebSocket 연결을 요청할 때 호출됩니다.
        """
        # Phase 2에서 인증/인가 로직이 추가될 부분입니다.
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        """
        클라이언트의 WebSocket 연결이 끊어졌을 때 호출됩니다.
        """
        # Phase 3에서 Channel Group 퇴장 및 DB 저장 로직이 추가될 부분입니다.
        pass

    async def receive(self, text_data: str) -> None:
        """
        클라이언트로부터 메시지를 수신했을 때 호출됩니다.
        """
        # Phase 2에서 메시지 저장 및 방송 로직이 추가될 부분입니다.
        pass