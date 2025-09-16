import json
import logging

import redis
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_search_logs import LectureSearchLog
from apps.lectures.models.user_prefer_categories import UserPreferCategory
from apps.lectures.serializers.crawled_lecture import LectureSerializer

from apps.lectures.services.lecture_list_service import get_lectures, filter_lectures, sort_lectures

logger = logging.getLogger(__name__)
# lecture 전체 가져오는 페이지네이션 가능한 제네릭뷰 1개
# 추천목록 3개 반환하는 API 1개 - 여기서만 하면 되겠죠

class RecommendLectureListView(APIView):

    serializer_class = LectureSerializer
    page_size = 10

    @extend_schema(
        tags=["Lectures"],
        summary="강의 목록 조회 및 검색/필터링/정렬",
        description="무한 스크롤, 검색, 필터링, 정렬 기능을 지원하는 강의 목록 API",
    )
    def get(self, request: Request) -> Response:
        return self.list(request)