from typing import TypedDict

from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer[Notification]):
    """
    알림 목록 조회를 위한 Serializer
    """

    notification_id = serializers.IntegerField(source="id", read_only=True)
    type = serializers.CharField(source="notification_type", read_only=True)

    class Meta:
        model = Notification
        fields = ["notification_id", "content", "type", "is_read", "back_url_link", "created_at"]


class NotificationUpdateSerializer(serializers.ModelSerializer[Notification]):
    """
    특정 알림 읽음 처리를 위한 Serializer (요청 본문용)
    """

    class Meta:
        model = Notification
        fields = ["is_read"]
        extra_kwargs = {"is_read": {"required": True}}


class UnreadCountOut(TypedDict):
    unread_count: int


class UnreadCountSerializer(serializers.Serializer[UnreadCountOut]):
    """
    읽지 않은 알림 수 조회를 위한 Serializer
    """

    unread_count = serializers.IntegerField()
