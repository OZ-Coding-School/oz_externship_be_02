from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_bookmarks import LectureBookmark


@extend_schema(
    tags=["강의"],
    summary="강의 북마크 추가 API",
    description="특정 강의를 북마크에 추가합니다.",
    responses={
        200: {"type": "object", "properties": {"lecture_id": {"type": "integer"}, "bookmarked": {"type": "boolean"}}},
    },
)
class BookmarkAddView(APIView):
    def post(self, request, lecture_id: int):
        try:
            lecture = Lecture.objects.get(pk=lecture_id)
        except Lecture.DoesNotExist:
            return Response({"error": "강의가 존재하지 않음"}, status=status.HTTP_404_NOT_FOUND)

        _, created = LectureBookmark.objects.get_or_create(user=request.user, lecture=lecture)
        if not created:
            return Response({"error": "이미 북마크됨"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"lecture_id": lecture_id, "bookmarked": True}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["강의"],
    summary="강의 북마크 해제 API",
    description="특정 강의를 북마크에서 삭제합니다.",
    responses={
        200: {"type": "object", "properties": {"lecture_id": {"type": "integer"}, "bookmarked": {"type": "boolean"}}},
    },
)
class BookmarkCancelView(APIView):
    def delete(self, request, lecture_id: int):
        try:
            lecture = Lecture.objects.get(pk=lecture_id)
        except Lecture.DoesNotExist:
            return Response({"error": "강의가 존재하지 않음"}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = LectureBookmark.objects.filter(user=request.user, lecture=lecture).delete()
        if not deleted:
            return Response({"error": "북마크가 존재하지 않음"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"lecture_id": lecture_id, "bookmarked": False}, status=status.HTTP_200_OK)
