from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_bookmarks import LectureBookmark


@extend_schema(
    tags=["강의"],
    summary="강의 북마크 추가 API",
    description="특정 강의를 북마크 하거나 북마크 해제합니다.",
    responses={
        200: {"type": "object", "properties": {"lecture_uuid": {"type": "string"}, "bookmarked": {"type": "boolean"}}},
    },
)
class BookmarkView(APIView):
    def post(self, request, lecture_uuid: str):
        try:
            lecture = Lecture.objects.get(pk=lecture_uuid)
        except Lecture.DoesNotExist:
            return Response({"error": "강의가 존재하지 않음"}, status=status.HTTP_404_NOT_FOUND)

        _, created = LectureBookmark.objects.get_or_create(user=request.user, lecture=lecture)
        if not created:
            return Response({"error": "이미 북마크됨"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"lecture_id": lecture_uuid, "bookmarked": True}, status=status.HTTP_200_OK)

    def delete(self, request, lecture_uuid: str):
        try:
            lecture = Lecture.objects.get(pk=lecture_uuid)
        except Lecture.DoesNotExist:
            return Response({"error": "강의가 존재하지 않음"}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = LectureBookmark.objects.filter(user=request.user, lecture=lecture).delete()
        if not deleted:
            return Response({"error": "북마크가 존재하지 않음"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"lecture_id": lecture_uuid, "bookmarked": False}, status=status.HTTP_200_OK)
