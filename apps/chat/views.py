from typing import cast

from django.db.models import Count, OuterRef, Prefetch, Q, Subquery
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..studies.models import StudyGroup
from ..users.models import User
from .models import ChatMessage, LastReadMessage
from .serializers import ChatRoomSerializer


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
                unread_message_count=Count(
                    "chat_messages", filter=Q(chat_messages__id__gt=last_read_message_id)  # 마지막 읽은 메시지 이후
                ),
            )
        )
        # 2. 시리얼라이저 호출 ( 위에서 가져온 스터디 그룹을 사용 )
        serializer = self.serializer_class(queryset, many=True)
        # 3. 시리얼라이저를 사용하여 응답 데이터 반환
        return Response(serializer.data, status=status.HTTP_200_OK)
