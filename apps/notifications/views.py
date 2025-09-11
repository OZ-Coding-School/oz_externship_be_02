from typing import Any, cast

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
    NotificationListQueryParamsSerializer,
    NotificationListSerializer,
    NotificationUpdateSerializer,
    UnreadCountOut,
    UnreadCountSerializer,
)
from apps.notifications.services.read_service import NotificationService
from apps.users.models.user import User


@extend_schema(
    tags=["Notifications"],
    summary="알림 목록 조회 API",
    description="로그인한 유저의 알림 내역을 페이지네이션으로 조회. status로 필터링",
    responses={200: NotificationListSerializer(many=True)},
)
class NotificationListView(ListAPIView[Notification]):
    """
    알림 목록 조회 with offset
    """

    serializer_class: type[NotificationListSerializer] = NotificationListSerializer
    pagination_class = NotificationLimitOffsetPagination
    permission_classes = [IsAuthenticated]
    validated_query_params: dict[str, Any]

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # 쿼리파라미터 검증
        qp = NotificationListQueryParamsSerializer(
            data=self.request.query_params
        )  # 본문 데이터가 request.query_params로 저장
        qp.is_valid(raise_exception=True)
        self.validated_query_params = qp.validated_data

        return super().list(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Notification]:
        user = cast(User, self.request.user)

        # 서비스 호출 (검증된 값만 전달)
        return NotificationService.get_notifications_list(user_id=user.id, **self.validated_query_params)


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

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, notification_id: int, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, request.user)
        NotificationService.read_notification(notification_id=notification_id, user_id=user.id)
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

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, request.user)
        NotificationService.read_all_user_notifications(user_id=user.id)
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

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, request.user)
        count = NotificationService.get_unread_count(user_id=user.id)
        payload: UnreadCountOut = {"unread_count": count}
        serializer = UnreadCountSerializer(instance=payload)
        return Response(serializer.data, status=status.HTTP_200_OK)
