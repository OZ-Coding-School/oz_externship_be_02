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

    def delete(self, request: Request, recruitment_id: int) -> Response:
        try:
            recruitment = Recruitment.objects.get(id=recruitment_id)
        except Recruitment.DoesNotExist:
            return Response({"detail": "Recruitment not found"}, status=status.HTTP_404_NOT_FOUND)

        recruitment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
