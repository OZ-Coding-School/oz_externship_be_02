from typing import cast

from django.core.exceptions import ValidationError
from django.db.models import Count, OuterRef, Prefetch, Q, Subquery
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..studies.models import StudyGroup
from ..users.models import User
from .models import ChatMessage, LastReadMessage
from .paginations import ChatMessageCursorPagination
from .permissions import IsMemberOnStudyGroup
from .serializers import (
    ChatMessageSerializer,
    ChatRoomSerializer,
)


class ChatRoomListView(APIView):
    """
    채팅방 목록 조회 API
    GET /api/v1/chat/rooms/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ChatRoomSerializer

    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        last_read_message_id = Subquery(
            LastReadMessage.objects.filter(user=user, study_group_id=OuterRef("pk")).values("message_id")[:1]
        )
        queryset = (
            StudyGroup.objects.prefetch_related(
                Prefetch(
                    "chat_messages",
                    queryset=ChatMessage.objects.order_by("-created_at"),
                ),
                "chat_messages__sender",
            )
            .filter(groupmember__user=user)
            .annotate(
                unread_message_count=Count("chat_messages", filter=Q(chat_messages__id__gt=last_read_message_id)),
            )
        )
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatMessageListView(APIView):
    """
    특정 채팅방의 메시지 목록 조회 API
    GET /api/v1/chat/rooms/{study_group_uuid}/messages
    """

    permission_classes = [IsAuthenticated, IsMemberOnStudyGroup]
    pagination_class = ChatMessageCursorPagination
    serializer_class = ChatMessageSerializer

    def get(self, request: Request, study_group_uuid: str) -> Response:
        # 채팅방 존재 여부 확인
        try:
            study_group = StudyGroup.objects.get(uuid=study_group_uuid)
        except StudyGroup.DoesNotExist:
            return Response({"error": "채팅방을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, study_group)

        # 기본 쿼리 (최신순)
        queryset = (
            ChatMessage.objects.select_related("sender").filter(study_group=study_group).order_by("-created_at", "-id")
        )

        # DRF CursorPagination 사용
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        # serializer로 변환
        serializer = ChatMessageSerializer(paginated_queryset, many=True)

        # DRF 표준 응답 반환
        return paginator.get_paginated_response(serializer.data)
