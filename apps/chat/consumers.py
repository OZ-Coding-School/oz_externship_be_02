# oz_externship_be/apps/chat/consumers.py
import json
import uuid
from typing import Any, Dict, Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AbstractBaseUser
from django.utils.timezone import localtime

from apps.chat.models import ChatMessage
from apps.studies.models import GroupMember, StudyGroup
from apps.users.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    """
    연결 시 사용자를 인증하고, 그룹 멤버십을 확인하며 메시지를 송수신
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.room_group_name: Optional[str] = None
        self.user: Optional[AbstractBaseUser] = None
        self.study_group_uuid: Optional[uuid.UUID] = None
        self.study_group: Optional[StudyGroup] = None

    async def connect(self) -> None:
        """
        WebSocket 연결 요청을 처리
        """
        self.study_group_uuid = self.scope["url_route"]["kwargs"]["study_group_uuid"]
        self.room_group_name = f"chat_{self.study_group_uuid}"

        self.user = self.scope.get("user")

        study_group = await self._get_study_group(self.study_group_uuid)
        if (
            self.user
            and self.user.is_authenticated
            and study_group
            and await self._is_member(self.user, study_group)
        ):
            self.study_group = study_group
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
        # '읽음 처리' 및 '온라인 상태' 업데이트 로직은 다음 이슈에서 이 메서드에 추가됩니다. 

    async def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None) -> None:
        """
        클라이언트로부터 메시지를 수신하고, 타입에 맞는 핸들러로 전달
        """
        if not text_data:
            return
        
        try:
            message = json.loads(text_data)
            handler_name = f"_handle_{message.get('type')}"
            handler = getattr(self, handler_name, self._handle_unknown_type)
            await handler(message.get("data", {}))
        except json.JSONDecodeError:
            await self._send_error_message("Invalid JSON format.")

    # -- Message Handlers --

    async def _handle_send_message(self, data: Dict[str, Any]) -> None:
        content = data.get("content")
        if content and self.user and self.study_group:
            new_message = await self._create_chat_message(
                sender=self.user,
                study_group=self.study_group,
                content=content,
            )

            created_at_kst = localtime(new_message.created_at).isoformat()

            message_data_to_broadcast = {
                "message_id": new_message.id,
                "sender": {
                    "user_uuid": str(new_message.sender.uuid),
                    "nickname": new_message.sender.nickname,
                    "profile_img_url": new_message.sender.profile_img_url,
                },
                "content": new_message.content,
                "created_at": created_at_kst,
            }

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "data": message_data_to_broadcast,
                },
            )

    async def _handle_unknown_type(self, data: Dict[str, Any]) -> None:
        await self._send_error_message(f"Unknown message type received.")

    # -- Event Handlers --

    async def chat_message(self, event: Dict[str, Any]) -> None:
        """
        'chat.message' 타입의 이벤트를 Channel Group으로부터 수신하여 클라이언트에게 전송
        """
        message_data = event["data"]
        await self.send(
            text_data=json.dumps({"type": "chat.message", "data": message_data})
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
        self, sender: User, study_group: StudyGroup, content: str
    ) -> ChatMessage:
        return ChatMessage.objects.create(
            sender=sender, study_group=study_group, content=content
        )

