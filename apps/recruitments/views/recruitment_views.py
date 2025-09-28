from typing import cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import filters, serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.authentications import JWTAuthenticationOrReadOnly
from apps.recruitments.managers.managers_list import RecruitmentListQuerySet
from apps.recruitments.serializers.recruitments_serializers import (
    RecruitmentCreateOutputSerializer,
    RecruitmentCreateSerializer,
)
from apps.recruitments.serializers.serializers_list import RecruitmentListSerializer
from apps.recruitments.services.services_list import (
    filter_is_closed,
    filter_tag,
    get_my_recm_list,
    get_recm_list,
)
from apps.users.models.user import User


class RecruitmentView(APIView):
    authentication_classes = (JWTAuthenticationOrReadOnly,) # 읽기에서는 JWTAuthentication None 반환

    # 검색정보
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["views_count", "bookmarks_count", "created_at"]

    @extend_schema(
        tags=["스터디 구인 공고"],
        summary="구인 공고 목록 조회",
        description="스터디 구인 공고 목록을 조회할 수 있습니다.\n\n"
        "<참고 사항> 이미지가 없을 경우 img키의 값이 None로 응답합니다. 이 경우 프론트엔드에서 기본 이미지를 처리해주세요.\n\n"
        "### 주요 기능\n\n"
        "1. 마감된 공고는 목록에 노출하지 않음\n\n"
        "2. 페이지네이션 기능\n\n"
        "3. 검색기능(공고 제목에서 검색)\n\n"
        "4. 필터링기능(카테고리, 사용자 정의 태그)\n\n"
        "5. 정렬 기능(최신순-기본, 조회수 높은 순, 북마크 순)",
        parameters=[
            OpenApiParameter(name="page", description="조회할 page", required=True, type=OpenApiTypes.INT),
            OpenApiParameter(
                name="size",
                description="조회할 page의 데이터 개수를 정할 수 있음\n\n" "정하지 않으면 기본으로 10개씩 반환함",
                required=False,
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="search",
                description="검색할 키워드를 입력",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="ordering",
                description="**'-views_count'**는 조회수 높은 순, **'-bookmarks_count'**는 북마크 많은 순\n\n"
                "입력하지 않으면 기본으로 최신 순으로 정렬\n\n"
                "같은 값들을 정렬 하려면 **-views_count,-created_at** 사용\n\n",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="tag",
                description="해당 태그를 가진 공고만 필터링",
                required=False,
                type=OpenApiTypes.STR,
            ),
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
    def get(self, request: Request) -> Response:
        # 조회
        get_list_queryset: RecruitmentListQuerySet = get_recm_list()

        # 필터
        # 'tag' 파라미터 확인
        tag = request.query_params.get("tag", None)
        if tag is not None and tag != "":
            get_list_queryset = filter_tag(get_list_queryset, tag)

        # 검색
        search_filter = filters.SearchFilter()
        searched_queryset = search_filter.filter_queryset(request, get_list_queryset, self)

        # 정렬
        ordering_filter = filters.OrderingFilter()
        ordering_queryset = ordering_filter.filter_queryset(request, searched_queryset, self)

        # 페이지네이션
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginator.page_size_query_param = "size"
        paginator.max_page_size = 100
        # url의 page파라미터를 읽어 데이터 슬라이싱
        paginated_queryset = paginator.paginate_queryset(ordering_queryset, request, self)

        serializer = RecruitmentListSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["스터디 구인 공고"],
        summary="구인 공고 작성",
        description="스터디 구인 공고 작성이 가능합니다.\n\n"
        "### 작성 제한\n\n"
        "1. 이미지 업로드( 최대 5개, 이미지 용량 5MB 이하 )\n\n"
        "2. 종료되지 않은 스터디 그룹에 대해서만 구인 공고 작성 가능\n\n"
        "3. 참고 파일 업로드 ( 최대 3개,  파일 용량 5MB 이하 )\n\n"
        "### 부가 기능\n\n"
        "예상 결제 비용을 별도로 미입력 시 강의 항목 당 결제 비용을 모두 합산하여 자동 입력",
        request=RecruitmentCreateSerializer,
        responses={
            201: RecruitmentCreateOutputSerializer,
            400: inline_serializer(
                name="error_validate",
                fields={
                    "attachments": serializers.CharField(default="첨부 파일은 최대 3개까지 등록 가능합니다."),
                    "study_group": serializers.CharField(default="종료된 스터디 그룹은 등록 불가능합니다."),
                },
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = RecruitmentCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        new_recm = serializer.save()
        return Response(RecruitmentCreateOutputSerializer(new_recm).data, status=status.HTTP_201_CREATED)


class MyRecruitmentView(APIView):
    permission_classes = [IsAuthenticated]

    # 필터 사용
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["views_count", "bookmarks_count", "created_at"]

    @extend_schema(
        tags=["스터디 구인 공고"],
        summary="내가 등록한 스터디 구인 공고 목록 조회",
        description="로그인 유저가 등록한 스터디 구인 공고의 목록을 조회할 수 있습니다.\n\n"
        "<참고 사항> 이미지가 없을 경우 img키의 값이 None로 응답합니다. 이 경우 프론트엔드에서 기본 이미지를 처리해주세요.\n\n"
        "### 주요 기능\n\n"
        "1. 페이지네이션 기능\n\n"
        "2. 필터링기능(마감됨, 모집중)\n\n"
        "3. 정렬 기능(최신순-기본, 조회수 높은 순, 북마크 순)\n\n",
        parameters=[
            OpenApiParameter(name="page", description="조회할 page", required=True, type=OpenApiTypes.INT),
            OpenApiParameter(
                name="size",
                description="조회할 page의 데이터 개수를 정할 수 있음\n\n" "정하지 않으면 기본으로 10개씩 반환함",
                required=False,
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="is_closed",
                description="마감여부 필터링(마감됨-True, 모집중-False)",
                required=False,
                type=OpenApiTypes.BOOL,
            ),
            OpenApiParameter(
                name="ordering",
                description="**'-views_count'**는 조회수 높은 순, **'-bookmarks_count'**는 북마크 많은 순\n\n"
                "입력하지 않으면 기본으로 최신 순으로 정렬\n\n"
                "같은 값들을 정렬 하려면 **-views_count,-created_at** 사용\n\n",
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={
            200: inline_serializer(
                name="get_my_pagelist",
                fields={
                    "count": serializers.IntegerField(default=100),
                    "next": serializers.URLField(default="https://api.example.org/accounts/?page=5"),
                    "previous": serializers.URLField(default="https://api.example.org/accounts/?page=3"),
                    "results": RecruitmentListSerializer(many=True),
                },
            ),
            400: inline_serializer(
                name="error_validate_is_closed",
                fields={"error": serializers.CharField(default="잘못된 is_closed 입력값")},
            ),
        },
    )
    def get(self, request: Request) -> Response:
        # 조회
        user = cast(User, request.user)
        get_mylist_queryset: RecruitmentListQuerySet = get_my_recm_list(user)

        # 필터
        is_closed = request.query_params.get("is_closed", None)
        if is_closed is not None and is_closed != "":
            if is_closed.lower() in ["true", "1"]:
                get_mylist_queryset = filter_is_closed(get_mylist_queryset, True)
            elif is_closed.lower() in ["false", "0"]:
                get_mylist_queryset = filter_is_closed(get_mylist_queryset, False)
            else:
                return Response({"error": "잘못된 is_closed 입력값"}, status=status.HTTP_400_BAD_REQUEST)

        # 정렬
        ordering_filter = filters.OrderingFilter()
        ordering_queryset = ordering_filter.filter_queryset(request, get_mylist_queryset, self)

        # 페이지네이션
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginator.page_size_query_param = "size"
        paginator.max_page_size = 100
        # url의 page파라미터를 읽어 데이터 슬라이싱
        paginated_queryset = paginator.paginate_queryset(ordering_queryset, request)

        serializer = RecruitmentListSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
