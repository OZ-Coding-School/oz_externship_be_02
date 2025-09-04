import json

import redis
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.serializers.crawled_lecture import LectureSerializer


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
        try:
            redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
            cached_lectures = redis_client.get("lectures:list")
        except redis.exceptions.ConnectionError:
            return Response({"detail": "Redis connection error"}, status=500)

        if cached_lectures:
            try:
                lectures = json.loads(cached_lectures)
            except json.JSONDecodeError:
                return Response({"detail": "Invalid cached data"}, status=500)
        else:
            # 🔥 캐시 없을 경우 DB에서 불러오기
            queryset = Lecture.objects.all()
            serializer = self.serializer_class(queryset, many=True)
            lectures = serializer.data
            redis_client.set("lectures:list", json.dumps(lectures))

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
        category = request.query_params.get("category")
        if category:
            lectures = [lec for lec in lectures if category in lec.get("categories", [])]
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
