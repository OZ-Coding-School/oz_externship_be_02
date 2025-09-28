from typing import Any, Union

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.services.admin_dashboard_services import (
    AdminDashboardPeriod,
    AdminDashboardService,
    WithdrawalReasonService,
)


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

        try:
            period = AdminDashboardPeriod(period_str)
        except ValueError:
            return Response(
                {"error": "period는 'monthly' 또는 'yearly'만 가능합니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        data = AdminDashboardService.get_signup_trends(period=period)
        return Response(data)


class WithdrawalTrendAPIView(APIView):
    permission_classes = [IsAdminUser]
    """
    월 단위, 연 단위 회원탈퇴 추세 데이터를 반환하는 API
    """

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
    def get(self, request: Request) -> Response:
        period_str = request.query_params.get("period", "monthly")

        try:
            period = AdminDashboardPeriod(period_str)
        except ValueError:
            return Response(
                {"error": "period는 'monthly' 또는 'yearly'만 가능합니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        data = AdminDashboardService.get_withdrawals_trends(period=period)
        return Response(data)


class WithdrawalReasonTrendAPIView(APIView):
    """
    회원 탈퇴 사유 통계 데이터를 반환하는 API
    원형 차트 : 전체 비율
    막대 그래프 : 월별 추세
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["관리자 API - 대시보드"],
        summary="회원탈퇴 사유 통계 조회",
        parameters=[
            OpenApiParameter(
                name="chart_type",
                type=str,
                required=True,
                enum=["pie", "bar"],
                description="조회할 차트 종류 ('pie' 또는 'bar')",
            ),
            OpenApiParameter(
                name="reason", type=str, description="막대 그래프 조회 시 특정 사유만 필터링 (예: 'OTHER')"
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        chart_type = request.query_params.get("chart_type")
        data: Union[dict[str, int], dict[str, dict[str, Any]]]

        if chart_type == "pie":
            data = WithdrawalReasonService.get_reason_pie_chart_data()
            return Response(data)

        elif chart_type == "bar":
            reason = request.query_params.get("reason")
            data = WithdrawalReasonService.get_reason_bar_chart_data(reason=reason)
            return Response(data)

        else:
            return Response(
                {"error": "chart_type은 'pie' 또는 'bar' 형식이어야 합니다."}, status=status.HTTP_400_BAD_REQUEST
            )
