from typing import cast

from django.db.models import OuterRef, QuerySet, Subquery
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.core.paginators import DefaultCursorPagination
from apps.recruitments.models import Recruitment
from apps.users.models import User

from ..models import Application
from ..serializers.applications_list_serializers import MyApplicationListSerializer


class MyApplicationsListView(generics.ListAPIView[Recruitment]):
    serializer_class = MyApplicationListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultCursorPagination

    def get_queryset(self) -> QuerySet[Recruitment]:
        user = cast(User, self.request.user)
        # 사용자가 지원한 공고에 대한 Application 객체를 서브쿼리로 조회
        user_applications = Application.objects.filter(recruitment=OuterRef("pk"), user=user)

        # 사용자가 지원한 모든 공고를 조회하고, 각 공고에 대해 사용자의 지원 상태와 지원 날짜를 annotate
        queryset = (
            Recruitment.objects.filter(applications__user=user)
            .annotate(
                user_application_status=Subquery(user_applications.values("status")[:1]),
                user_applied_at=Subquery(user_applications.values("created_at")[:1]),
            )
            .prefetch_related("tags", "study_group__lectures", "images")
            .distinct()
        )
        return queryset
