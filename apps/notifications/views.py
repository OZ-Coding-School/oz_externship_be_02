from typing import Any

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.pagination import NotificationLimitOffsetPagination
from apps.notifications.serializers import (
    NotificationSerializer,
    NotificationUpdateSerializer,
    UnreadCountOut,
    UnreadCountSerializer,
)

STATUS_ALL = "all"
STATUS_UNREAD = "unread"
STATUS_READ = "read"


@extend_schema(
    tags=["Notifications"],
    summary="알림 목록 조회 API",
    description="로그인한 유저의 알림 내역을 페이지네이션으로 조회. status로 필터링",
    responses={200: NotificationSerializer(many=True)},
)
class NotificationListView(ListAPIView[Notification]):
    """
    알림 목록 조회 with offset
    """

    serializer_class: type[NotificationSerializer] = NotificationSerializer
    pagination_class = NotificationLimitOffsetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Notification]:
        assert self.request.user.is_authenticated  # 인증 유저가 아니면 AssertionError를 발생시켜 요청 처리를 중단
        qs = (
            Notification.objects.filter(user_id=self.request.user.pk)
            .only("id", "content", "notification_type", "is_read", "back_url_link", "created_at")
            .order_by("-created_at", "-id")
        )

        status = self.request.query_params.get("status", "all")
        if status == "unread":
            qs = qs.filter(is_read=False)
        elif status == "read":
            qs = qs.filter(is_read=True)

        return qs


@extend_schema(
    tags=["Notifications"],
    summary="특정 알림 읽음 처리 API",
    description="특정 알림의 is_read 상태를 true로 변경",
    request=NotificationUpdateSerializer,
    responses={204: None},
)
class NotificationUpdateView(APIView):
    """
    특정 알림 읽음 처리
    """

    def post(self, request: Request, notification_id: int, *args: Any, **kwargs: Any) -> Response:
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Notifications"],
    summary="모든 알림 일괄 읽음 처리 API",
    description="로그인한 유저의 모든 읽지 않은 알림을 읽음 상태로 변경",
    responses={204: None},
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
        mock_count: UnreadCountOut = {"unread_count": 5}

        serializer = UnreadCountSerializer(instance=mock_count)
        return Response(serializer.data, status=status.HTTP_200_OK)
