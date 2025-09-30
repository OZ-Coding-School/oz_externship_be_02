import json
import logging
from typing import Any

import redis
from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_search_logs import LectureSearchLog
from apps.lectures.serializers.crawled_lecture import LectureSerializer

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60 * 24


class LectureCursorPagination(CursorPagination):

    page_size: int = 10
    page_size_query_param: str = "size"
    max_page_size: int = 5000
    ordering: tuple[str, str] = ("-updated_at", "-pk")


@extend_schema(
    tags=["Lectures"],
    parameters=[
        OpenApiParameter(
            name="cursor", description="다음/이전 페이지를 위한 커서 값", required=False, type=OpenApiTypes.STR
        ),
        OpenApiParameter(name="size", description="페이지 당 항목 수", required=False, type=OpenApiTypes.INT),
        OpenApiParameter(
            name="search", description="강의명 또는 강사명으로 검색", required=False, type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="category", description="카테고리 name으로 필터링 (콤마로 구분)", required=False, type=OpenApiTypes.STR
        ),
    ],
    summary="[Cursor Pagination] 강의 목록 조회",
    description="무한 스크롤에 최적화된 커서 기반 페이지네이션을 사용합니다.",
)
class LectureListView(ListAPIView[Lecture]):
    serializer_class = LectureSerializer
    pagination_class = LectureCursorPagination

    @method_decorator(cache_page(CACHE_TTL))
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Lecture]:
        search_keyword: str = self.request.query_params.get("search") or ""
        category_param = self.request.query_params.get("category")

        if self.request.user.is_authenticated and search_keyword:
            try:
                LectureSearchLog.objects.create(user=self.request.user, keyword=search_keyword.lower())
            except Exception as e:
                logger.error("Failed to save search log for user %s: %s", self.request.user.id, str(e))

        queryset: QuerySet[Lecture] = Lecture.objects.search(search_keyword).filter_by_categories(category_param)
        return queryset
