import logging

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.crawled_lecture_reviews import LectureReview
from apps.lectures.serializers.lecture_review import LectureReviewSerializer

logger = logging.getLogger(__name__)


class LectureReviewsView(APIView):
    serializer_class = LectureReviewSerializer

    @extend_schema(
        tags=["Lectures"],
        summary="강의 리뷰 조회",
        description="DB에서 직접 강의 리뷰를 조회합니다.",
    )
    def get(self, request: Request, lecture_uuid: str) -> Response:
        # DB에서 바로 조회
        queryset = LectureReview.objects.filter(lecture__uuid=lecture_uuid)
        serializer = self.serializer_class(queryset, many=True)
        lecture_reviews = serializer.data


        # 리뷰 없으면 빈 결과 반환
        if not lecture_reviews:
            return Response({"results": [], "next": None, "previous": None})

        return Response({"results": lecture_reviews})
