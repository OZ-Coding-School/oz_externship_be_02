from typing import Callable, cast

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.services.admin_dashboard_services import AdminDashboardService, Period


@extend_schema(
    tags=["관리자 페이지 API - 대시보드"],
    summary="회원가입 추세 조회",
    description="연, 월 단위로 회원가입 추세를 조회합니다.",
    parameters=[
        OpenApiParameter(
            name="period",
            type=str,
            description="조회 기간 단위, 'monthly', 'yearly'를 입력합니다.",
            required=False,
            default="monthly",
            enum=["monthly", "yearly"],
        )
    ],
    responses={200: {"description": "성공", "example": {"2025-08": 10, "2025-09": 15}}},
)
class SignUpTrendAPIView(APIView):
    permission_classes = [IsAdminUser]
    """
    월 단위, 연 단위 회원가입 추세 데이터를 반환하는 API
    """

    def get(self, request: Request) -> Response:
        period_str = request.query_params.get("period", "monthly")
        if period_str not in ["monthly", "yearly"]:
            return Response(
                {"error": "period는 'monthly' 또는 'yearly'만 가능합니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        period = cast(Period, period_str)
        data = AdminDashboardService.get_signup_trends(period=period)
        return Response(data)


@extend_schema(
    tags=["관리자 페이지 API - 대시보드"],
    summary="회원탈퇴 추세 조회",
    description="연, 월 단위로 회원탈퇴 추세를 조회합니다.",
    parameters=[
        OpenApiParameter(
            name="period",
            type=str,
            description="조회 기간 단위, 'monthly', 'yearly'를 입력합니다.",
            required=False,
            default="monthly",
            enum=["monthly", "yearly"],
        )
    ],
    responses={200: {"description": "성공", "example": {"2025-07": 2, "2025-08": 5}}},
)
class WithdrawalTrendAPIView(APIView):
    permission_classes = [IsAdminUser]
    """
    월 단위, 연 단위 회원탈퇴 추세 데이터를 반환하는 API
    """

    def get(self, request: Request) -> Response:
        period_str = request.query_params.get("period", "monthly")
        if period_str not in ["monthly", "yearly"]:
            return Response(
                {"error": "period는 'monthly' 또는 'yearly'만 가능합니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        period = cast(Period, period_str)
        data = AdminDashboardService.get_withdrawals_trends(period=period)
        return Response(data)
