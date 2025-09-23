from __future__ import annotations

import uuid
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import CursorPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_bookmarks import LectureBookmark
from apps.lectures.serializers.bookmark_serializers import LectureBookmarkListSerializer
from apps.users.models.user import User as UserModel


class BookmarkView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["강의"],
        summary="강의 북마크 추가",
        description="특정 강의를 북마크합니다.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "lecture_uuid": {"type": "string"},
                    "bookmarked": {"type": "boolean"},
                },
            }
        },
    )
    def post(self, request: Request, lecture_uuid: uuid.UUID) -> Response:
        lecture = get_object_or_404(Lecture, uuid=lecture_uuid)
        user = cast(UserModel, request.user)
        LectureBookmark.objects.get_or_create(user=user, lecture=lecture)
        return Response(
            {"lecture_uuid": str(lecture_uuid), "bookmarked": True},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["강의"],
        summary="강의 북마크 삭제",
        description="특정 강의의 북마크를 해제합니다.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "lecture_uuid": {"type": "string"},
                    "bookmarked": {"type": "boolean"},
                },
            }
        },
    )
    def delete(self, request: Request, lecture_uuid: uuid.UUID) -> Response:
        lecture = get_object_or_404(Lecture, uuid=lecture_uuid)
        user = cast(UserModel, request.user)
        LectureBookmark.objects.filter(user=user, lecture=lecture).delete()
        return Response(
            {"lecture_uuid": str(lecture_uuid), "bookmarked": False},
            status=status.HTTP_200_OK,
        )


def _extract_cursor(link: str | None, param: str = "cursor") -> str | None:
    """DRF의 get_next_link()/get_previous_link()가 만들어주는 URL에서 cursor 토큰만 추출."""
    if not link:
        return None
    parsed = urlparse(link)
    qs = parse_qs(parsed.query)
    vals = qs.get(param)
    return vals[0] if vals else None


class BookmarkCursorPagination(CursorPagination):
    ordering = ("-created_at", "-pk")
    page_size: int = 10
    page_size_query_param: str = "page_size"
    cursor_query_param: str = "cursor"

    # 🔄 응답에서 next/previous URL을 제거하고 cursor 값만 내려줌
    def get_paginated_response(self, data: list[dict[str, Any]]) -> Response:
        next_link = self.get_next_link()
        prev_link = self.get_previous_link()
        return Response(
            {
                "next_cursor": _extract_cursor(next_link, self.cursor_query_param),
                "previous_cursor": _extract_cursor(prev_link, self.cursor_query_param),
                "results": data,
            },
            status=status.HTTP_200_OK,
        )


class BookmarkListView(ListAPIView[LectureBookmark]):
    """
    GET /api/v1/lectures/bookmarks
    - 커서 기반 페이지네이션
    - 응답: {"next_cursor": "...", "previous_cursor": "...", "results": [...]}
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LectureBookmarkListSerializer
    pagination_class = BookmarkCursorPagination

    @extend_schema(
        tags=["강의"],
        summary="강의 북마크 목록 조회",
        description="로그인 사용자의 강의 북마크 목록을 커서 기반으로 페이지네이션하여 반환합니다.",
        parameters=[
            OpenApiParameter(name="cursor", type=str, location="query", required=False),
            OpenApiParameter(name="page_size", type=int, location="query", required=False),
            OpenApiParameter(name="search", type=str, location="query", required=False),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "next_cursor": {"type": ["string", "null"]},
                    "previous_cursor": {"type": ["string", "null"]},
                    "results": {"type": "array", "items": {"type": "object"}},
                },
            }
        },
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[LectureBookmark]:
        user = cast(UserModel, self.request.user)
        qs: QuerySet[LectureBookmark] = (
            LectureBookmark.objects.filter(user=user).select_related("lecture").order_by("-created_at", "-pk")
        )

        keyword = self.request.query_params.get("search")
        if keyword:
            qs = qs.filter(Q(lecture__title__icontains=keyword) | Q(lecture__instructor__icontains=keyword))
        return qs
