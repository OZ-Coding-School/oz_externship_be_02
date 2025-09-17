from __future__ import annotations

import uuid
from typing import Any, List, cast

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_bookmarks import LectureBookmark
from apps.lectures.serializers.bookmark_serializers import BookmarkListItemSerializer
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
                "properties": {"lecture_uuid": {"type": "string"}, "bookmarked": {"type": "boolean"}},
            }
        },
    )
    def post(self, request: Request, lecture_uuid: uuid.UUID) -> Response:
        lecture = get_object_or_404(Lecture, uuid=lecture_uuid)
        user = cast(UserModel, request.user)
        LectureBookmark.objects.get_or_create(user=user, lecture=lecture)
        return Response({"lecture_uuid": str(lecture_uuid), "bookmarked": True}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["강의"],
        summary="강의 북마크 삭제",
        description="특정 강의의 북마크를 해제합니다.",
        responses={
            200: {
                "type": "object",
                "properties": {"lecture_uuid": {"type": "string"}, "bookmarked": {"type": "boolean"}},
            }
        },
    )
    def delete(self, request: Request, lecture_uuid: uuid.UUID) -> Response:
        lecture = get_object_or_404(Lecture, uuid=lecture_uuid)
        user = cast(UserModel, request.user)
        LectureBookmark.objects.filter(user=user, lecture=lecture).delete()
        return Response({"lecture_uuid": str(lecture_uuid), "bookmarked": False}, status=status.HTTP_200_OK)


class BookmarkListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # CursorPagination 교체
    class Pagination(CursorPagination):
        ordering = "-created_at"
        page_size: int = 10
        page_size_query_param: str = "page_size"
        cursor_query_param: str = "cursor"

    @extend_schema(
        tags=["강의"],
        summary="강의 북마크 목록 조회",
        description="내가 북마크한 강의 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(name="cursor", type=str, location="query", required=False),
            OpenApiParameter(name="page_size", type=int, location="query", required=False),
            OpenApiParameter(name="search", type=str, location="query", required=False),
        ],
        responses={200: {"type": "object"}},
    )
    def get(self, request: Request) -> Response:
        user = cast(UserModel, request.user)

        qs = (
            LectureBookmark.objects
            .filter(user=user)
            .select_related("lecture")
        )

        # 검색 강의,강사
        keyword = request.query_params.get("search")
        if keyword:
            qs = qs.filter(
                Q(lecture__title__icontains=keyword) |
                Q(lecture__instructor__icontains=keyword)
            )

        paginator = self.Pagination()
        page_qs = paginator.paginate_queryset(qs, request, view=self)

        # page_qs는 LectureBookmark들의 리스트
        lectures: List[Lecture] = [lb.lecture for lb in (page_qs or [])]
        serializer = BookmarkListItemSerializer(lectures, many=True)

        return paginator.get_paginated_response(serializer.data)
