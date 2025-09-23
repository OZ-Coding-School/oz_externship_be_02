from pydoc import describe
from typing import Any, Type, Union

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.filters import WithdrawalFilter
from apps.users.models import Withdrawals
from apps.users.serializers.admin_withdrawal_serializers import (
    AdminWithdrawalDetailSerializer,
    AdminWithdrawalListSerializer,
)
from apps.users.views.admin_views import UserAdminPagination


@extend_schema_view(
    list=extend_schema(
        tags=["회원 관리 페이지 API - 회원 탈퇴 관리"],
        summary="회원 탈퇴 내역 목록 조회",
        description="회원 탈퇴를 신청한 유저 내역을 조회합니다.",
    ),
    retrieve=extend_schema(
        tags=["회원 관리 페이지 API - 회원 탈퇴 관리"],
        summary="회원 탈퇴 내역 상세 조회",
        description="특정 회원의 탈퇴 내역 상세 정보를 조회합니다.",
    ),
)
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

    @extend_schema(
        tags=["회원 관리 페이지 API - 회원 탈퇴 관리"],
        summary="탈퇴 회원 복구",
        description="탈퇴 신청한 회원의 계정의 상태를 다시 활성화(is_active) 상태로 복구합니다.",
        request=None,
        responses={200: {"description": "성공 메시지", "example": {"message": "유저 복구가 완료 되었습니다."}}},
    )

    # restore 요청에 복구 로직을 구현
    @action(detail=True, methods=["post"])
    def restore(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        URL: POST /api/v1/admin/withdrawals/{id}/restore
        선택한 탈퇴 유저를 복구
        """
        with transaction.atomic():
            withdrawal = self.get_object()
            user = withdrawal.user

            withdrawal.delete()

            user.is_active = True
            user.save(update_fields=["is_active", "updated_at"])

        return Response({"message": "유저 복구가 완료 되었습니다."})
