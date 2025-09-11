import typing

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recruitments.managers.managers_list import RecruitmentListQuerySet
from apps.recruitments.serializers.serializers_list import RecruitmentListSerializer
from apps.recruitments.services.services_list import active_get_query


class RecruitmentView(APIView):
    # swagger 테스트를 위해 사용
    permession_class = [AllowAny]

    @extend_schema(
        tags=["스터디 구인 공고"],
        summary="구인 공고 목록 조회",
        description="모든 유저는 스터디 구인 공고 메뉴에 접속하여 등록된 스터디 구인 공고들을 가로로 긴 카드 형태의 목록으로 확인할 수 있습니다.\n\n"
        "<참고 사항> 이미지가 없을 경우 img키의 값이 None로 응답합니다. 이 경우 프론트엔드에서 기본 이미지를 처리해주세요.\n\n"
        "### 주요 기능\n\n"
        "1. 마감된 공고는 목록에 노출하지 않음\n\n"
        "2. 페이지네이션 기능\n\n"
        "3. 검색기능(공고 제목에서 검색)\n\n"
        "4. 필터링기능(카테고리, 사용자 정의 태그)\n\n"
        "5. 정렬 기능(최신순-기본, 조회수 높은 순, 북마크 순)",
        parameters=[
            OpenApiParameter(name="page", description="조회할 page", required=True, type=OpenApiTypes.INT),
            OpenApiParameter(name="size", description="조회할 page의 데이터 개수를 정할 수 있음", required=False, type=OpenApiTypes.INT)
        ],
        responses={
            200: inline_serializer(
                name="get_pagelist",
                fields={
                    "count": serializers.IntegerField(default=100),
                    "next": serializers.URLField(default="https://api.example.org/accounts/?page=5"),
                    "previous": serializers.URLField(default="https://api.example.org/accounts/?page=3"),
                    "results": RecruitmentListSerializer(many=True),
                },
            )
        },
    )
    def get(self: typing.Self, request: Request) -> Response:
        # 조회
        optimized_queryset: RecruitmentListQuerySet = active_get_query()

        # 페이지네이션
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginator.page_size_query_param='size'
        paginator.max_page_size=100
        # url의 page파라미터를 읽어 데이터 슬라이싱
        paginated_queryset = paginator.paginate_queryset(optimized_queryset, request)

        serializer = RecruitmentListSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
