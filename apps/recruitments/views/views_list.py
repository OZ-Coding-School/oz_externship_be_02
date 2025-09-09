import typing

from django.db.models import Count, OuterRef, Subquery
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recruitments.models.recruitment_images import RecruitmentImage
from apps.recruitments.models.recruitments import Recruitment
from apps.recruitments.serializers.serializers_list import RecruitmentListSerializer


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
        responses={status.HTTP_200_OK:RecruitmentListSerializer(many=True)},
    )
    def get(self: typing.Self, request: Request) -> Response:
        # 마감된 공고는 필터하고 최신순을 기본 정렬로 함
        queryset = Recruitment.objects.filter(is_closed=False).order_by("-created_at")
        # 시리얼라이저에 필요한 정보 채우기
        # outerref : https://www.reddit.com/r/django/comments/q40km4/help_understanding_outerref/?tl=ko
        img_subquery = RecruitmentImage.objects.filter(recruitment=OuterRef("id")).values("img_url")[:1]
        optimized_queryset = (
            queryset.annotate(img=Subquery(img_subquery), bookmarks_count=Count("bookmark_users", distinct=True))
            .select_related("study_group")
            .prefetch_related("study_group__lectures", "tags")
        )

        serializer = RecruitmentListSerializer(optimized_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
