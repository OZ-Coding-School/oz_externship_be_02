from __future__ import annotations

import uuid
from typing import cast

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_bookmarks import LectureBookmark
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
