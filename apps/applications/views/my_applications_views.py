from typing import cast

from django.db.models import QuerySet
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.core.paginators import DefaultCursorPagination
from apps.users.models import User

from ..models import Application
from ..serializers.applications_list_serializers import MyApplicationListSerializer
from ..services import ApplicationService


class MyApplicationsListView(generics.ListAPIView[Application]):
    serializer_class = MyApplicationListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultCursorPagination

    def get_queryset(self) -> QuerySet[Application]:
        service = ApplicationService()
        user = cast(User, self.request.user)
        return service.get_my_applications(user=user)
