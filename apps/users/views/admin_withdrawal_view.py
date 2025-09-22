from typing import Type, Union

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAdminUser

from apps.users.filters import WithdrawalFilter
from apps.users.models import Withdrawals
from apps.users.serializers.admin_withdrawal_serializers import (
    AdminWithdrawalDetailSerializer,
    AdminWithdrawalListSerializer,
)
from apps.users.views.admin_views import UserAdminPagination


class WithdrawalAdminViewSet(viewsets.ReadOnlyModelViewSet[Withdrawals]):
    """
    관리자 페이지 회원 탈퇴 내역 LIST 조회 API
    """

    queryset = Withdrawals.objects.select_related("user").all().order_by("-created_at")
    permission_classes = [IsAdminUser]

    pagination_class = UserAdminPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]

    filterset_class = WithdrawalFilter
    search_fields = ["user__email", "user__name", "user__nickname"]
    ordering_fields = ["created_at", "due_date", "user__name", "user__email"]

    def get_serializer_class(self) -> Type[Union[AdminWithdrawalDetailSerializer, AdminWithdrawalListSerializer]]:
        if self.action == "retrieve":
            return AdminWithdrawalDetailSerializer
        return AdminWithdrawalListSerializer
