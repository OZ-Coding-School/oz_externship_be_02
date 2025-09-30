from django.contrib.auth.models import AnonymousUser
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.services.recommend_lecture_service import RecommendLectureService


class RecommendLectureListView(APIView):
    page_size = 3

    @extend_schema(
        tags=["Lectures"],
        summary="강의 목록 조회 및 추천",
        description="무한 스크롤, 검색, 필터링, 정렬 기능을 지원하는 강의 목록 API",
    )
    def get(self, request: Request) -> Response:
        service = RecommendLectureService()
        lectures = Lecture.objects.all()

        # Serializer로 dict 리스트 변환
        lectures_data = list(service.serializer_class(lectures, many=True).data)

        user = request.user
        if isinstance(user, AnonymousUser):
            # 로그인 안된 경우 상위 page_size 강의 반환
            recommended_lectures = lectures_data[: service.page_size]
        else:
            # 로그인 유저이면 추천 로직 실행
            recommended_lectures = service.preferred_lectures(user, lectures_data)

        return Response({"results": recommended_lectures})
