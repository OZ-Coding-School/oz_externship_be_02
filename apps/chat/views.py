from typing import cast, Any
from django.db.models import Count, OuterRef, Prefetch, Q, Subquery
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..studies.models import StudyGroup
from ..users.models import User
from .models import ChatMessage, LastReadMessage
from .serializers import ChatRoomSerializer, ApiChatMessageSerializer
import base64

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

class ChatMessageListView(APIView):
    # 특정 채팅방의 메시지 목록 조회 API
    # GET /api/v1/chat/rooms/{study_group_uuid}/messages/

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, study_group_uuid: str) -> Response:
        user = cast(User, request.user)

        # 쿼리 파라미터
        cursor = request.GET.get('cursor')

        # 메시지 조회 개수 설정
        if not cursor:
            # 최초 접속
            fetch_limit = 300
        else:
            # 무한 스크롤 100개
            fetch_limit = 100

        # 채팅방 존재 여부 및 접근 권한 확인 (채팅방에 접속한 유저만)
        try:
            study_group = StudyGroup.objects.get(
                uuid=study_group_uuid,
                groupmember__user=user
        )
        except StudyGroup.DoesNotExist:
            return Response(
                {"error": "채팅방을 찾을 수 없거나 접근 권한이 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 기본 쿼리셋 (최신순)
        queryset = (
            ChatMessage.objects
            .select_related("sender")
            .filter(study_group = study_group)
            .order_by("-created_at", "-id")
        )

        # 이전 메시지들 조회-무한 스크롤용
        if cursor:
            try:
                cursor_data = base64.b64decode(cursor.encode()).decode()
                cursor_id = int(cursor_data.split('_')[1])

                # 오래된 이전 메시지들
                queryset = queryset.filter(id__lt=cursor_id)
            except (ValueError, IndexError):
                pass


            # fetch_limit + 1개 가져와서 다음 페이지 존재 여부 확인
        messages = list(queryset[:fetch_limit + 1])

        # 다음 페이지의 여부를 확인하는 코드
        has_next = len(messages) > fetch_limit
        if has_next:
            messages = messages[:fetch_limit]

        # 메시지를 시간순으로 뒤집기 (오래된 것부터 -> 최신순으로) (위쪽이 오래된 메시지 아래가 최신순)
        messages.reverse()

        next_cursor = None
        if has_next and messages:
            oldest_message = messages[0]
            cursor_string = f"c_{oldest_message.id}"
            next_cursor = base64.b64encode(cursor_string.encode()).decode()

            # API 명세서에 맞는 serializer 사용 (is_my_message 포함)
        serializer = ApiChatMessageSerializer(
            messages,
            many=True,
            context={'request': request} # 본인 메시지인지 구분하기 위해 사용
        )

            # 응답 데이터 구성
        response_data: dict[str, Any] = {
            "results": serializer.data,
            "fetch_info": {
                "fetched_count": len(messages),
                "is_initial_load": not cursor,
                "fetch_limit": fetch_limit
                }
            }

        if next_cursor:
            response_data["next_cursor"] = next_cursor

        return Response(response_data, status=status.HTTP_200_OK)