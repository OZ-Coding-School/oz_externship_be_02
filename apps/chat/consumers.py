# oz_externship_be/apps/chat/consumers.py
import json
import logging
import uuid
from typing import Any, Dict, Optional, Union, cast

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.utils.timezone import localtime

from apps.chat.models import ChatMessage
from apps.studies.models import GroupMember, StudyGroup
from apps.users.models import User

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    연결 시 사용자를 인증하고 그룹을 확인하며 메시지를 송수신
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.room_group_name: Optional[str] = None
        self.user: Union[AbstractBaseUser, AnonymousUser, None] = None
        self.study_group_uuid: Optional[uuid.UUID] = None
        self.study_group: Optional[StudyGroup] = None

    async def connect(self) -> None:
        """
        WebSocket 연결 요청을 처리하고, 성공 시 입장 이벤트
        """
        self.study_group_uuid = self.scope["url_route"]["kwargs"]["study_group_uuid"]
        self.room_group_name = f"chat_{self.study_group_uuid}"
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        study_group = await self._get_study_group(self.study_group_uuid)
        if not study_group or not await self._is_member(cast(User, self.user), study_group):
            await self.close(code=4003)
            return

        self.study_group = study_group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # 새로운 사용자의 입장을 그룹에 알림
        if self.room_group_name:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user.event",
                    "data": {
                        "event_type": "join",
                        "user": {
                            "user_uuid": str(self.user.uuid),
                            "nickname": self.user.nickname,
                        },
                    },
                },
            )

    async def disconnect(self, close_code: int) -> None:
        """
        WebSocket 연결이 끊어졌을 때, 퇴장 이벤트를 방송하고 그룹에서 퇴장
        """
        if self.room_group_name and self.user and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user.event",
                    "data": {
                        "event_type": "leave",
                        "user": {
                            "user_uuid": str(self.user.uuid),
                            "nickname": self.user.nickname,
                        },
                    },
                },
            )
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None) -> None:
        if not text_data:
            return
        try:
            message = json.loads(text_data)
            handler_name = f"_handle_{message.get('type')}"
            handler = getattr(self, handler_name, self._handle_unknown_type)
            await handler(message.get("data", {}))
        except json.JSONDecodeError as e:
            # JSON 파싱 오류 시 로그 기록
            logger.warning(f"WebSocket: JSON decode error from {self.user}: {e}")
            await self._send_error_message("잘못된 JSON 형식입니다.")

    # -- Message Handlers --

    async def _handle_send_message(self, data: Dict[str, Any]) -> None:
        content = data.get("content")

        # content의 유효성 검증
        if not content or not content.strip():
            await self._send_error_message("메시지 내용은 비어 있을 수 없습니다.")
            return
        if len(content) > 500: 
            await self._send_error_message("메시지 내용은 500자를 초과할 수 없습니다.")
            return

        new_message = await self._create_chat_message(
            sender=cast(User, self.user),
            study_group=self.study_group,
            content=content,
        )

        if new_message.sender and self.room_group_name:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "data": {
                        "message_id": new_message.id,
                        "sender": {
                            "user_uuid": str(new_message.sender.uuid),
                            "nickname": new_message.sender.nickname,
                            "profile_img_url": new_message.sender.profile_img_url,
                        },
                        "content": new_message.content,
                        "created_at": localtime(new_message.created_at).isoformat(),
                    },
                },
            )

    async def _handle_unknown_type(self, data: Dict[str, Any]) -> None:
        logger.warning(f"WebSocket: Unknown message type received from {self.user}")
        await self._send_error_message("알 수 없는 메시지 타입입니다.")

    # -- Event Handlers --

    async def chat_message(self, event: Dict[str, Any]) -> None:
        await self.send(
            text_data=json.dumps({"type": "chat.message", "data": event["data"]})
        )
    
    async def user_event(self, event: Dict[str, Any]) -> None:
        """'user.event' 타입의 이벤트를 클라이언트에게 전송"""
        await self.send(
            text_data=json.dumps({"type": "user.event", "data": event["data"]})
        )

    # -- Helper methods --

    async def _send_error_message(self, message: str, code: int = 4000) -> None:
        await self.send(
            text_data=json.dumps(
                {"type": "error.message", "data": {"code": code, "message": message}}
            )
        )

    @database_sync_to_async
    def _get_study_group(self, study_group_uuid: uuid.UUID) -> Optional[StudyGroup]:
        try:
            return StudyGroup.objects.get(uuid=study_group_uuid)
        except StudyGroup.DoesNotExist:
            return None

    @database_sync_to_async
    def _is_member(self, user: User, study_group: StudyGroup) -> bool:
        return GroupMember.objects.filter(study_group=study_group, user=user).exists()

    @database_sync_to_async
    def _create_chat_message(
        self, sender: User, study_group: Optional[StudyGroup], content: str
    ) -> ChatMessage:
        return ChatMessage.objects.create(
            sender=sender, study_group=study_group, content=content
        )

