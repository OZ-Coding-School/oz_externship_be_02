from typing import cast

from rest_framework import filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.serializers.admin_application_serializers import (
    ApplicationAdminSerializer,
)
from apps.applications.services.admin_application_services import (
    check_permission,
    filter_status,
    get_admin_application_list,
)
from apps.users.models.user import User


class AdminApplicationsAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["recruitment__title", "user__nickname", "user__email"]
    ordering_fields = ["created_at"]

    def get(self, request: Request) -> Response:
        request.user = cast(User, request.user)
        if not check_permission(request.user):
            raise PermissionDenied

        # 조회
        get_list_queryset = get_admin_application_list()

        # 필터
        status = request.query_params.get("status", None)
        if status is not None and status != "":
            get_list_queryset = filter_status(get_list_queryset, status)

        # 검색
        search_filter = filters.SearchFilter()
        searched_queryset = search_filter.filter_queryset(request, get_list_queryset, self)

        # 정렬
        ordering_filter = filters.OrderingFilter()
        ordering_queryset = ordering_filter.filter_queryset(request, searched_queryset, self)

        # 페이지네이션
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginator.max_limit = 100
        paginated_queryset = paginator.paginate_queryset(ordering_queryset, request, self)

        serializer = ApplicationAdminSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
