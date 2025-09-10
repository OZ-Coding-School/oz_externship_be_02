from datetime import date, timedelta

from apps.users.models.user import User
from apps.users.models.withdrawals import Withdrawals


def create_withdrawal(user: User, reason: str, reason_detail: str) -> Withdrawals:
    """
    회원 탈퇴 요청을 생성하는 비즈니스 로직을 처리.
    1. 탈퇴 처리 마감일(due_date)을 계산
    2. Withdrawals 모델 인스턴스를 생성하고 저장
    """
    # 비즈니스 로직 1: 탈퇴 처리 마감일은 14일 뒤로 설정
    due_date = date.today() + timedelta(days=14)

    # 비즈니스 로직 2: 모델 객체 생성
    withdrawal = Withdrawals.objects.create(user=user, reason=reason, reason_detail=reason_detail, due_date=due_date)

    return withdrawal
