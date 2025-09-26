from enum import Enum
from typing import Type, Union

from django.db.models import Count
from django.db.models.functions import Trunc

from apps.users.models import User, Withdrawals


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
