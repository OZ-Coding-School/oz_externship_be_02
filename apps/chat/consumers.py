# oz_externship_be/apps/chat/consumers.py
import json
import uuid
from typing import Any, Dict, Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AbstractBaseUser

from apps.studies.models import StudyGroup, GroupMember
from apps.users.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    """
    연결 시 사용자를 인증하고, 그룹 멤버십을 확인
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.room_group_name: Optional[str] = None
        self.user: Optional[AbstractBaseUser] = None
        self.study_group_uuid: Optional[uuid.UUID] = None

    async def connect(self) -> None:
        """
        WebSocket 연결 요청을 처리합니다.
        """
        self.study_group_uuid = self.scope["url_route"]["kwargs"]["study_group_uuid"]
        self.room_group_name = f"chat_{self.study_group_uuid}"

        self.user = self.scope.get("user")

        if (
            self.user
            and self.user.is_authenticated
            and await self.is_member(self.user, self.study_group_uuid)
        ):
            await self.channel_layer.group_add(
                self.room_group_name, self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code: int) -> None:
        """
        클라이언트의 WebSocket 연결이 끊어졌을 때 호출
        """
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data: str) -> None:
        """
        클라이언트로부터 메시지를 수신했을 때 호출 (다음 이슈에서 구현 예정)
        """
        pass

    @database_sync_to_async
    def is_member(self, user: User, study_group_uuid: uuid.UUID) -> bool:
        """
        사용자가 특정 스터디 그룹의 멤버인지 비동기적으로 확인
        """
        try:
            study_group = StudyGroup.objects.get(uuid=study_group_uuid)
            return GroupMember.objects.filter(
                study_group=study_group, user=user
            ).exists()
        except StudyGroup.DoesNotExist:
            return False