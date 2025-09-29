from rest_framework import serializers
from rest_framework.pagination import CursorPagination
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

class ChatMessageCursorPagination(CursorPagination):
    # 채팅 메시지용 커서 페이지 네이션
    page_size = 100
    ordering = 'created_at'
    cursor_query_param = 'cursor'
    page_size_query_param = 'page_size'
    max_page_size = 300

class ChatRoomSerializer(serializers.ModelSerializer[StudyGroup]):
    last_message = ChatMessageSerializer(
        source="chat_messages.first", read_only=True
    )  # 가장 최근에 온 메세지(content) # 상황에 따라서 view에서 처리 (N+1 문제 방지)
    unread_message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = StudyGroup
        fields = ["uuid", "name", "unread_message_count", "last_message"]


class SenderSerializer(serializers.ModelSerializer[User]):
    user_uuid = serializers.UUIDField(source="uuid", read_only=True)
    profile_img_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["uuid", "nickname", "profile_img_url"]
        extra_kwargs = {"uuid": {"read_only": True}}

    def get_profile_img_url(self, obj: User) -> str:
        if hasattr(obj, "profile_image") and obj.profile_image:
            return f"~/profiles/{obj.uuid}.png"
        return f"~/profiles/default.png"  # 기본 이미지


class ApiChatMessageSerializer(serializers.ModelSerializer[ChatMessage]):
    message_id = serializers.IntegerField(source="id", read_only=True)
    sender = SenderSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ["message_id", "sender", "content", "created_at"]
