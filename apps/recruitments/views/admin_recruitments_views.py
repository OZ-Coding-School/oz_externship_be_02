from django.db import models
from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from apps.recruitments.filtering import CustomRecruitmentFilter
from apps.recruitments.models import Recruitment
from apps.recruitments.serializers.recruitments_serializers import (
    AdminRecruitmentListSerializer,
)


class AdminRecruitmentListView(generics.ListAPIView[Recruitment]):
    serializer_class = AdminRecruitmentListSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self) -> models.QuerySet[Recruitment]:
        base_queryset = Recruitment.admin_objects.get_admin_listings()

        # 커스텀 필터 클래스를 사용하여 필터링 로직 위임
        custom_filter = CustomRecruitmentFilter(request=self.request, queryset=base_queryset)
        return custom_filter.filter_queryset()
