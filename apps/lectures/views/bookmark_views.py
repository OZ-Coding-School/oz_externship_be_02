from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_bookmarks import LectureBookmark
from apps.lectures.serializers.bookmark_serializers import (
    BookmarkToggleRequestSerializer,
    BookmarkToggleResponseSerializer,
)


@extend_schema(
    tags=["강의 관리"],
    summary="강의 북마크 등록/해제",
    description=(
        "로그인 사용자가 특정 강의를 북마크에 등록하거나 해제합니다.\n"
        "- 북마크가 없으면 등록, 있으면 해제됩니다.\n"
        "- `lecture_id`는 정수 PK입니다."
    ),
    request=BookmarkToggleRequestSerializer,
    responses={
        200: BookmarkToggleResponseSerializer,
        400: {"type": "object", "properties": {"error": {"type": "string"}}},
        404: {"type": "object", "properties": {"error": {"type": "string"}}},
    },
)
class BookmarkToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 요청 바디 검증
        s = BookmarkToggleRequestSerializer(data=request.data)
        if not s.is_valid():
            return Response({"error": s.errors}, status=status.HTTP_400_BAD_REQUEST)

        lecture_id = s.validated_data["lecture_id"]

        # 강의 조회
        try:
            lecture = Lecture.objects.get(pk=lecture_id)
        except Lecture.DoesNotExist:
            return Response({"error": "강의가 존재하지 않음"}, status=status.HTTP_404_NOT_FOUND)

        # 토글
        bookmark, created = LectureBookmark.objects.get_or_create(user=request.user, lecture=lecture)
        if created:
            data = {"lecture_id": lecture_id, "bookmarked": True}
        else:
            bookmark.delete()
            data = {"lecture_id": lecture_id, "bookmarked": False}

        return Response(BookmarkToggleResponseSerializer(data).data, status=status.HTTP_200_OK)
