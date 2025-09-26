from datetime import timedelta, datetime
from rest_framework import serializers
from django.utils import timezone
from ..studies.models import StudyGroup
from ..users.models import User
from .models import ChatMessage, LastReadMessage
from ..users.tests.test_admin import user_model


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

class SenderSerializer(serializers.ModelSerializer[User]):
    profile_img_url = serializers.SerializerMethodField()
    class Meta:
        models = User
        fields = ["uuid", "nickname", "profile_img_url"]
        extra_kwargs = {
            "uuid": {"read_only": True}
        }

    def get_profile_img_url(self, obj: User) -> str:
        if hasattr(obj, 'profile_image') and obj.profile_image:
            return f"~/profiles/{obj.uuid}.png"
        return f"~/profiles/{obj.uuid}.png" # 기본 이미지


class ApiChatMessageSerializer(serializers.ModelSerializer[ChatMessage]):
    message_id = serializers.IntegerField(source='id', read_only= True)
    sender = SenderSerializer(read_only = True)

    class Meta:
        models = ChatMessage
        fields = ["message_id", "sender", "content", "create_at"]

class ChatMessageDetailSerializer(serializers.ModelSerializer[ChatMessage]):
    sender = SenderInfoSerializer(read_only=True)
    time_display = serializers.SerializerMethodField()
    sender_name = serializers.SerializerMethodField()
    study_group_info = serializers.SerializerMethodField()
    is_read_by_me = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ["id", "name", "content", "created_at", "sender_name", "study_group_info", "time_display", "is_read_by_me"]

    def get_time_display(self, obj: ChatMessage) -> str:
        now = timezone.now()
        created_at = obj.created_at
        diff = now - created_at

        if diff < timedelta(minutes=1):
            return "방금 전"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds()/ 60)
            return f"{minutes}분 전"
        elif diff < timedelta(hours=24):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}시간 전"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days}일 전"
        else:
            return created_at.strftime("%Y-%m-%d")

    def get_sender_name(self, obj: ChatMessage) -> str:
        # 발신자 이름
        if obj.sender :
            return obj.sender.nickname or obj.sender.name or "사용자"
        return "알 수 없는 사용자"

    def get_study_group_info(self, obj: ChatMessage) -> dict[str, str]:
        # 메시지가 속한 채팅방 정보
        return {
            "uuid" : str(obj.study_group.uuid),
            "name" : obj.study_group.name
        }

    def get_is_read_by_me(self, obj: ChatMessage) -> bool:
        # 현재 사용자의 읽음 상태 확인
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        try:
            last_read = LastReadMessage.objects.get(
                user = request.user,
                study_group = obj.study_group
            )
            return obj.id <= last_read.message_id
        except LastReadMessage.DoesNotExist:
        # 읽은 기록이 없으면 모든 메시지를 읽지 않음 처리
            return False
