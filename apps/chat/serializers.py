from rest_framework import serializers

from ..studies.models import StudyGroup
from ..users.models import User
from .models import ChatMessage


class SenderInfoSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["uuid", "nickname", "name", "gender"]


class ChatMessageSerializer(serializers.ModelSerializer[ChatMessage]):
    sender = SenderInfoSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ["id", "content", "sender", "created_at"]


class ChatRoomSerializer(serializers.ModelSerializer[StudyGroup]):
    last_message = ChatMessageSerializer(
        source="chat_messages.first", read_only=True
    )  # 가장 최근에 온 메세지(content) # 상황에 따라서 view에서 처리 (N+1 문제 방지)
    unread_message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = StudyGroup
        fields = ["uuid", "name", "unread_message_count", "last_message"]
