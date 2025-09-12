import json
import logging

import redis
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.serializers.crawled_lecture import LectureSerializer

logger = logging.getLogger(__name__)


class LectureListView(APIView):

    serializer_class = LectureSerializer
    page_size = 10

    @extend_schema(
        tags=["Lectures"],
        parameters=[
            OpenApiParameter(name="page", description="페이지 번호", required=False, type=OpenApiTypes.INT),
            OpenApiParameter(
                name="search", description="강의명 또는 강사명으로 검색", required=False, type=OpenApiTypes.STR
            ),
            OpenApiParameter(
                name="category", description="카테고리 name로 필터링", required=False, type=OpenApiTypes.STR
            ),
            OpenApiParameter(
                name="ordering",
                description="정렬 기준: price_asc, price_desc, rating_asc, rating_desc, oldest",
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        summary="강의 목록 조회 및 검색/필터링/정렬",
        description="무한 스크롤, 검색, 필터링, 정렬 기능을 지원하는 강의 목록 API",
    )
    def get(self, request: Request) -> Response:
        lectures = None
        redis_client = None

        try:
            redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
            cached_lectures = redis_client.get("lectures:list")
            if cached_lectures:
                try:
                    lectures = json.loads(cached_lectures)
                except json.JSONDecodeError:
                    logger.warning("\nLectureLog: Redis cached data invalid, fallback to DB")
        except redis.exceptions.ConnectionError as e:
            logger.error("\nLectureLog: Redis connection failed, fallback to DB: %s", str(e))

        if lectures is None:
            queryset = Lecture.objects.all()
            serializer = self.serializer_class(queryset, many=True)
            lectures = serializer.data

            if redis_client:
                try:
                    redis_client.set("lectures:list", json.dumps(lectures))
                except redis.exceptions.ConnectionError:
                    logger.warning("\nLectureLog: Failed to set lectures in Redis cache, skipping")

        # Filtering & Sorting
        lectures = self.filter_lectures(lectures, request)  # type: ignore
        lectures = self.sort_lectures(lectures, request.query_params.get("ordering"))  # type: ignore

        # Pagination
        page_number = request.query_params.get("page", 1)
        page_obj, paginator = self.paginate(lectures, self.page_size, page_number)  # type: ignore

        if not page_obj:
            return Response({"results": [], "next": None, "previous": None})

        return Response(
            {
                "count": paginator.count,
                "next": page_obj.next_page_number() if page_obj.has_next() else None,
                "previous": page_obj.previous_page_number() if page_obj.has_previous() else None,
                "results": list(page_obj),
            }
        )

    ###########################
    #### Functionalization ####
    ###########################

    def filter_lectures(self, lectures, request):  # type: ignore
        search = request.query_params.get("search")
        if search:
            search = search.lower()
            lectures = [
                lec for lec in lectures if search in lec["title"].lower() or search in lec["instructor"].lower()
            ]
        category_names = request.query_params.get("category")
        if category_names:

            names_to_filter = [name.strip() for name in category_names.split(",")]
            category_ids = Category.objects.filter(name__in=names_to_filter).values_list("id", flat=True)

            lectures = [lec for lec in lectures if any(cat_id in lec.get("categories", []) for cat_id in category_ids)]
        return lectures

    def sort_lectures(self, lectures, ordering):  # type: ignore
        if ordering == "price_asc":
            return sorted(lectures, key=lambda lec: lec.get("original_price") or 0)
        elif ordering == "price_desc":
            return sorted(lectures, key=lambda lec: lec.get("original_price") or 0, reverse=True)
        elif ordering == "rating_asc":
            return sorted(lectures, key=lambda lec: lec.get("average_rating") or 0)
        elif ordering == "rating_desc":
            return sorted(lectures, key=lambda lec: lec.get("average_rating") or 0, reverse=True)
        elif ordering == "oldest":
            return sorted(lectures, key=lambda lec: lec.get("updated_at") or "")
        else:
            return sorted(lectures, key=lambda lec: lec.get("updated_at") or lec.get("created_at"), reverse=True)

    def paginate(self, queryset, page_size, page_number):  # type: ignore
        paginator = Paginator(queryset, page_size)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            return None, paginator
        return page_obj, paginator
