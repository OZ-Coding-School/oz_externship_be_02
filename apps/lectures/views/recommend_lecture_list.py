import logging

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.services.recommend_lecture_service import RecommendLectureService
from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.serializers.crawled_lecture import LectureSerializer

logger = logging.getLogger(__name__)


class RecommendLectureListView(APIView):
    serializer_class = LectureSerializer
    page_size = 3

    @extend_schema(
        tags=["Lectures"],
        summary="강의 목록 조회 및 검색/필터링/정렬",
        description="무한 스크롤, 검색, 필터링, 정렬 기능을 지원하는 강의 목록 API",
    )
    def get(self, request: Request) -> Response:
        # 1️⃣ RecommendLectureService에서 추천 강의 가져오기
        service = RecommendLectureService()
        lectures = Lecture.objects.all()
        recommended_lectures = service.preferred_lectures(request, lectures)

        # 2️⃣ Serializer로 직렬화
        serializer = self.serializer_class(recommended_lectures, many=True)
        return Response({"results": serializer.data})