from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.serializers.crawled_lecture import LectureSerializer


class LectureListView(APIView):
    # 레디스 있는지 없는지 부터 검사
    # 있으면 레디스에서 없으면 디비에서
    serializer_class = LectureSerializer
    pagination_class = Paginator
    page_size = 10

    # Parameter In SwaggerUI
    @extend_schema(
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

        # Sorting
        lectures = Lecture.objects.all().order_by("-created_at")  # Default

        search_query = request.query_params.get("search", None)
        if search_query:
            lectures = lectures.filter(Q(title__icontains=search_query) | Q(instructor__icontains=search_query))
        category_name = request.query_params.get("category", None)
        if category_name:
            lectures = lectures.filter(categories__name=category_name)
        ordering_query = request.query_params.get("ordering", None)
        if ordering_query:
            if ordering_query == "price_asc":
                lectures = lectures.order_by("original_price")
            elif ordering_query == "price_desc":
                lectures = lectures.order_by("-original_price")
            elif ordering_query == "rating_asc":
                lectures = lectures.order_by("average_rating")
            elif ordering_query == "rating_desc":
                lectures = lectures.order_by("-average_rating")
            elif ordering_query == "oldest":
                lectures = lectures.order_by("created_at")

        # PageNation
        paginator = self.pagination_class(lectures, self.page_size)
        page_number = request.query_params.get("page", 1)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            return Response({"results": [], "next": None, "previous": None})

        # Results
        serializer = self.serializer_class(page_obj, many=True)

        return Response(
            {
                "count": paginator.count,
                "next": page_obj.next_page_number() if page_obj.has_next() else None,
                "previous": page_obj.previous_page_number() if page_obj.has_previous() else None,
                "results": serializer.data,
            }
        )
