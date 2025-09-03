import datetime
from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.serializers import (
    NotificationSerializer,
    NotificationUpdateSerializer,
    UnreadCountSerializer,
)


@extend_schema(
    tags=["Notifications"],
    summary="알림 목록 조회 API",
    description="로그인한 유저의 알림 내역을 페이지네이션으로 조회. status와 type으로 필터링",
)
class NotificationListView(APIView):
    """
    알림 목록 조회
    """

    serializer_class = NotificationSerializer

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        mock_notifications = [
            {
                "notification_id": 101,
                "content": "'Python 기초 스터디' 공고에 새로운 지원자가 있습니다.",
                "type": Notification.NotificationType.ADD_APPLICATION,
                "is_read": False,
                "back_url_link": "/recruitments/a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6/applications",
                "created_at": datetime.datetime.now() - datetime.timedelta(hours=2),
            },
            {
                "notification_id": 100,
                "content": "'알고리즘 스터디'에 새로운 멤버가 참여했습니다.",
                "type": Notification.NotificationType.STUDY_JOIN,
                "is_read": True,
                "back_url_link": "/studies/p6o5n4m3-l2k1-j0i9-h8g7-f6e5d4c3b2a1/chat",
                "created_at": datetime.datetime.now() - datetime.timedelta(days=2),
            },
        ]
        # Mock API 단계에서는 Serializer를 통과시키지 않고 직접 반환
        return Response(mock_notifications)


@extend_schema(
    tags=["Notifications"],
    summary="특정 알림 읽음 처리 API",
    description="특정 알림의 is_read 상태를 true로 변경",
    request=NotificationUpdateSerializer,
    responses={200: NotificationSerializer},
)
class NotificationUpdateView(APIView):
    """
    특정 알림 읽음 처리
    """

    def patch(self, request: Request, notification_id: int, *args: Any, **kwargs: Any) -> Response:
        mock_updated_notification = {
            "notification_id": notification_id,
            "content": "'Python 기초 스터디' 공고에 새로운 지원자가 있습니다.",
            "type": Notification.NotificationType.ADD_APPLICATION,
            "is_read": True,
            "back_url_link": "/recruitments/a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6/applications",
            "created_at": datetime.datetime.now() - datetime.timedelta(hours=2),
        }
        # Mock API 단계에서는 Serializer를 통과시키지 않고 직접 반환
        return Response(mock_updated_notification)


@extend_schema(
    tags=["Notifications"],
    summary="모든 알림 일괄 읽음 처리 API",
    description="로그인한 유저의 모든 읽지 않은 알림을 읽음 상태로 변경",
)
class NotificationReadAllView(APIView):
    """
    모든 알림 일괄 읽음 처리
    """

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Notifications"],
    summary="읽지 않은 알림 수 조회 API",
    description="로그인한 유저의 읽지 않은 알림 수를 조회 (보류된 기능)",
    responses={200: UnreadCountSerializer},
)
class UnreadCountView(APIView):
    """
    읽지 않은 알림 수 조회
    """

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        mock_count = {"unread_count": 5}
        # Mock API 단계에서는 Serializer를 통과시키지 않고 직접 반환
        return Response(mock_count)
