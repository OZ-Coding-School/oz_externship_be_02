import json
import logging

import redis
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
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
        description="캐시를 사용하며 Redis 문제 발생 시 DB fallback",
    )
    def get(self, request: Request, lecture_uuid: str) -> Response:

        redis_client = None
        cached_lecture_reviews = None

        # Redis 연결 시도
        try:
            redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
            cached_lecture_reviews = redis_client.get(f"lectures:reviews:{lecture_uuid}")
        except redis.exceptions.ConnectionError as e:
            logger.warning("\nLectureReviewLog: Redis connection failed, fallback to DB: %s", str(e))
            cached_lecture_reviews = None

        # 캐시 데이터 사용
        if cached_lecture_reviews:
            try:
                lecture_reviews = json.loads(cached_lecture_reviews)
            except json.JSONDecodeError:
                logger.warning("\nLectureReviewLog: Invalid cached data, fallback to DB")
                cached_lecture_reviews = None
                lecture_reviews = None

        # 캐시 없거나 오류 시 DB 조회
        if not cached_lecture_reviews:
            queryset = LectureReview.objects.filter(lecture__uuid=lecture_uuid)
            serializer = self.serializer_class(queryset, many=True)
            lecture_reviews = serializer.data
            for review in lecture_reviews:
                review["lecture"] = str(review["lecture"])
            # 캐시에 저장, Redis 문제 있어도 무시
            if redis_client:
                try:
                    redis_client.set(f"lectures:reviews:{lecture_uuid}", json.dumps(lecture_reviews), ex=600)
                except redis.exceptions.ConnectionError:
                    logger.warning("\nLectureReviewLog: Failed to set lecture reviews in Redis, skipping")

        # 리뷰 없으면 빈 결과
        if not lecture_reviews:
            return Response({"results": [], "next": None, "previous": None})

        return Response({"results": lecture_reviews})
