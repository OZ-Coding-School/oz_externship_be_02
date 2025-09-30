from django.db import models
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recruitments.filtering import CustomRecruitmentFilter
from apps.recruitments.models import Recruitment
from apps.recruitments.serializers.admin_recruitments_serializers import (
    AdminRecruitmentDetailSerializer,
)
from apps.recruitments.serializers.recruitments_serializers import (
    AdminRecruitmentListSerializer,
)
from apps.recruitments.services.recruitments_services import (
    get_recruitment_detail_for_admin,
)


from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema


@extend_schema(
    summary="[어드민] 구인 공고 목록 조회",
    tags=["어드민/구인 공고"],
    parameters=[
        OpenApiParameter(name="search", description="공고 제목 키워드", type=str),
        OpenApiParameter(name="status", description="공고 상태 필터링 (recruiting, closed)", type=str),
        OpenApiParameter(name="tags", description="필터링할 태그 ID (쉼표로 구분, 예: 1,5,10)", type=str),
        OpenApiParameter(name="ordering", description="정렬 기준 (created_at, -created_at, views_count, -views_count, bookmark_count, -bookmark_count)", type=str),
        OpenApiParameter(name="limit", description="한 페이지에 표시할 항목의 수", type=int),
        OpenApiParameter(name="offset", description="시작 위치 (0부터 시작)", type=int),
    ],
    responses={status.HTTP_200_OK: AdminRecruitmentListSerializer(many=True)},
)
class AdminRecruitmentListView(generics.ListAPIView[Recruitment]):
    serializer_class = AdminRecruitmentListSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self) -> models.QuerySet[Recruitment]:
        base_queryset = Recruitment.admin_objects.get_admin_listings()

        # 커스텀 필터 클래스를 사용하여 필터링 로직 위임
        custom_filter = CustomRecruitmentFilter(request=self.request, queryset=base_queryset)
        return custom_filter.filter_queryset()


class AdminRecruitmentDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request, recruitment_id: int) -> Response:
        recruitment = get_recruitment_detail_for_admin(recruitment_id=recruitment_id)
        serializer = AdminRecruitmentDetailSerializer(recruitment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 삭제
    def delete(self, request: Request, recruitment_id: int) -> Response:
        try:
            recruitment = Recruitment.objects.get(id=recruitment_id)
        except Recruitment.DoesNotExist:
            return Response({"detail": "Recruitment not found"}, status=status.HTTP_404_NOT_FOUND)

        recruitment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
