from typing import cast

from django.db.models import QuerySet
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.core.paginators import DefaultCursorPagination
from apps.users.models import User

from ..models import Application
from ..serializers.applications_list_serializers import MyApplicationListSerializer


class MyApplicationsListView(generics.ListAPIView[Application]):
    serializer_class = MyApplicationListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultCursorPagination

    def get_queryset(self) -> QuerySet[Application]:
        user = cast(User, self.request.user)
        queryset = (
            Application.objects.filter(user=user)
            .select_related("recruitment")
            .prefetch_related(
                "recruitment__tags",
                "recruitment__study_group__lectures",
                "recruitment__images",
            )
        )
        return queryset
