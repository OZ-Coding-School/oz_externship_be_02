from typing import Any, cast
from uuid import UUID

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.paginators import DefaultCursorPagination
from apps.recruitments.serializers.bookmark_serializers import (
    MyBookmarkedRecruitmentListSerializer,
)
from apps.recruitments.services.bookmark_services import BookmarkService
from apps.users.models import User


class BookmarkToggleView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["스터디 구인 공고/북마크"],
        summary="스터디 구인 공고 북마크 추가",
        description="특정 스터디 구인 공고를 북마크합니다. 이미 북마크된 경우에도 성공으로 응답합니다.",
        responses={
            201: inline_serializer(name="BookmarkCreated", fields={"detail": serializers.CharField()}),
            200: inline_serializer(name="BookmarkAlreadyExists", fields={"detail": serializers.CharField()}),
            404: inline_serializer(name="RecruitmentNotFound", fields={"error": serializers.CharField()}),
        },
    )
    def post(self, request: Request, recruitment_uuid: UUID) -> Response:
        service = BookmarkService()
        # 서비스단에서 생성된 상세 예외 메시지를 그대로 클라이언트에게 전달한다.
        try:
            _, created = service.add(user=cast(User, request.user), recruitment_uuid=recruitment_uuid)
            if created:
                return Response({"detail": "북마크가 추가되었습니다."}, status=status.HTTP_201_CREATED)
            return Response({"detail": "이미 북마크되어 있습니다."}, status=status.HTTP_200_OK)
        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["스터디 구인 공고/북마크"],
        summary="스터디 구인 공고 북마크 삭제",
        description="특정 스터디 구인 공고의 북마크를 해제합니다.",
        responses={
            204: None,
            404: inline_serializer(name="BookmarkNotFound", fields={"error": serializers.CharField()}),
        },
    )
    def delete(self, request: Request, recruitment_uuid: UUID) -> Response:
        service = BookmarkService()
        # 서비스단에서 생성된 상세 예외 메시지를 그대로 클라이언트에게 전달한다.
        try:
            service.remove(user=cast(User, request.user), recruitment_uuid=recruitment_uuid)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class MyBookmarkedRecruitmentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="북마크한 공고 목록 조회",
        tags=["스터디 구인 공고/북마크"],
        parameters=[
            OpenApiParameter(name="cursor", description="다음 페이지를 가리키는 커서 값", type=str),
            OpenApiParameter(name="limit", description="한 페이지에 표시할 항목의 수", type=int),
        ],
        responses={status.HTTP_200_OK: MyBookmarkedRecruitmentListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        service = BookmarkService()
        queryset = service.get_bookmarked_list(user=cast(User, request.user))

        paginator = DefaultCursorPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        serializer = MyBookmarkedRecruitmentListSerializer(paginated_queryset, many=True)
        paginated_data = cast(list[dict[str, Any]], serializer.data)
        return paginator.get_paginated_response(paginated_data)
