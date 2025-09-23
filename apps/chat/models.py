# oz_externship_be/apps/chat/models.py
from django.db import models

from apps.core.models.base import BaseModel
from apps.studies.models import StudyGroup
from apps.users.models import User


class ChatMessage(BaseModel):
    sender = models.ForeignKey(
        "users.User",
        # 유저가 삭제되면 채팅방에서 알수없는 사용자로 표기
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_chat_messages",
    )
    study_group = models.ForeignKey(
        "studies.StudyGroup",
        # 스터디 그룹이 삭제되면 메시지도 함께 삭제
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    content = models.CharField(max_length=500)

    def __str__(self) -> str:
        # 발신자 닉네임이 없는 경우를 대비하여 표시
        sender_nickname = self.sender.nickname if self.sender else "Unknown User"
        return f"Message from {sender_nickname} in {self.study_group.name}"

    class Meta:
        db_table = "chat_messages"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["study_group", "-created_at"]),
        ]


class LastReadMessage(BaseModel):
    message_id = models.BigIntegerField()
    user = models.ForeignKey(User, related_name="last_read_messages", on_delete=models.CASCADE)
    study_group = models.ForeignKey(StudyGroup, related_name="last_read_informations", on_delete=models.CASCADE)

    class Meta:
        db_table = "last_group_messages"

        indexes = [
            models.Index(fields=["study_group", "user"]),
        ]
