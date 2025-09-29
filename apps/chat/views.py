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
from .serializers import ApiChatMessageSerializer, ChatRoomSerializer, ChatMessageCursorPagination


class ChatRoomListView(APIView):
    """
    채팅방 목록 조회 API
    GET /api/v1/chat/rooms/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ChatRoomSerializer

    def get(self, request: Request, study_group_uuid: str) -> Response:
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
    pagination_class = ChatMessageCursorPagination

    def get(self, request: Request, study_group_uuid: str) -> Response:
        user = cast(User, request.user)

        # 채팅방 죤재 여부 확인
        try:
            study_group = StudyGroup.objects.get(uuid= study_group_uuid)
        except StudyGroup.DoesNotExist:
            return Response(
                {"error": "채팅방을 찾을 수 없습니다."},
                status= status.HTTP_404_NOT_FOUND
            )

        # 접근 권한 확인 (채팅방 멤버인지 유무 확인)
        if not study_group.groupmember_set.filter(user=user).exists():
            return Response(
                {"error": "채팅방에 접근 권한이 없습니다."},
                status= status.HTTP_403_FORBIDDEN
            )

        # 기본 쿼리 (최신순)
        queryset = (
            ChatMessage.objects
            .select_related("sender")
            .filter(study_group=study_group)
            .order_by("-created_at", "-id")
        )
        # DRF CursorPagination 사용
        paginator = self.pagination_class()

        # 최초 접속시 메시지 조회 (300개)
        cursor = request.GET.get('cursor')
        if not cursor:
            paginator.page_size = 300
        else:
            # 무한 스크롤 100개
            paginator.page_size = 100

        try:
            paginated_queryset = paginator.paginate_queryset(queryset, request, view= self)

            # None 체크도 try 안에서
            if paginated_queryset is None:
                return Response(
                    {"error": "페이지네이션 처리 중 오류가 발생했습니다."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except (ValidationError, ValueError, TypeError) as e:
            # 잘못된 커서의 경우
            return Response(
                {"error": "유효하지 않은 커서입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # serializer로 변환
        serializer = ApiChatMessageSerializer(
            paginated_queryset,
            many=True,
            context={'request': request}
        )

        # DRF의 get_paginated_response 사용
        # 기본 응답에 추가 필드 넣기
        response = paginator.get_paginated_response(serializer.data)

        # 응답 데이터에 채팅방 정보 추가
        response.data.update({
            "uuid": str(study_group.uuid),
            "name": study_group.name,
            "unread_message_count": 0
        })

        # results를 message로 키 이름 변경
        response.data['messages'] = response.data.pop('results')

        return response