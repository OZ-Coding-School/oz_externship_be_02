from datetime import timedelta
from enum import Enum
from typing import Any, Type, Union

from django.db.models import Count
from django.db.models.functions import Trunc, TruncMonth
from django.utils import timezone

from apps.users.models import User, Withdrawals, WithdrawalsReasonChoices


class AdminDashboardPeriod(Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class AdminDashboardService:
    @staticmethod
    # 비공개 헬퍼 메소드
    def _get_trends_by_model(model: Type[Union[User, Withdrawals]], period: AdminDashboardPeriod) -> dict[str, int]:
        """
        비공개 헬퍼, 특정 모델의 생성일 기준 추세를 집계
        """

        # 1. 설정한 기간에 따라 Trunc 단위를 결정
        trunc_kind = "month" if period == AdminDashboardPeriod.MONTHLY else "year"

        # 2. User 모델의 created_at 필드를 월, 년 단위로 나눠 회원 수를 카운트
        trends = (
            model.objects.annotate(period=Trunc("created_at", trunc_kind))
            .values("period")
            .annotate(count=Count("id"))
            .order_by("period")
        )

        # 3. 결과를 "날짜 : 가입자 수" 형태의 딕셔너리로 반환
        result = {item["period"].strftime("%Y-%m" if trunc_kind == "month" else "%Y"): item["count"] for item in trends}
        return result

    @staticmethod
    # 회원 가입 추세 집계
    def get_signup_trends(period: AdminDashboardPeriod) -> dict[str, int]:
        # 비공개 헬퍼 메소드에 User 모델을 전달해서 호출
        return AdminDashboardService._get_trends_by_model(User, period)

    @staticmethod
    # 회원 탈퇴 추세 집계
    def get_withdrawals_trends(period: AdminDashboardPeriod) -> dict[str, int]:
        # 비공개 헬퍼 메소드에 Withdrawals 모델을 전달하여 호출
        return AdminDashboardService._get_trends_by_model(Withdrawals, period)


class WithdrawalReasonService:
    @staticmethod
    def get_reason_pie_chart_data() -> dict[str, dict[str, Any]]:
        """
        전체 탈퇴 사유의 비율을 집계해서 원형 차트용 데이터 반환
        """
        total_count = Withdrawals.objects.count()
        if total_count == 0:
            return {}

        # 1. 탈퇴 사유별로 그룹화해서 카운트
        reason_counts = Withdrawals.objects.values("reason").annotate(count=Count("id")).order_by("-count")

        # 2. 사유코드 : (count:5, percentage:50.0) 형태로 데이터 가공
        pie_chart_data = {
            item["reason"]: {"count": item["count"], "percentage": round((item["count"] / total_count) * 100, 2)}
            for item in reason_counts
        }
        return pie_chart_data

    @staticmethod
    def get_reason_bar_chart_data(reason: str | None = None) -> dict[str, int]:
        """
        최근 12개월간의 월별 탈퇴 사유를 집계해 막대 그래프 데이터로 반환
        """

        # 1. 12개월 전의 날짜를 계산
        twelve_months_ago = timezone.now() - timedelta(days=365)

        # 2. 최근 12개월 데이터 필터링
        queryset = Withdrawals.objects.filter(created_at__gte=twelve_months_ago)

        # 3. 특정 사유가 파라미터로 요청되면, 해당 사유만 필터링
        if reason and reason in WithdrawalsReasonChoices.values:
            queryset = queryset.filter(reason=reason)

        # 4. 월별로 그룹화하여 개수를 카운트
        trends = (
            queryset.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        # 5. YYYY-MM: count 형태로 가공
        return {item["month"].strftime("%Y-%m"): item["count"] for item in trends}
