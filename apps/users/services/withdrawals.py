# apps/users/services/withdrawals.py

from datetime import date, timedelta

from apps.users.models.user import User
from apps.users.models.withdrawals import Withdrawals
from django.core.exceptions import ObjectDoesNotExist


def create_withdrawal(user: User, reason: str, reason_detail: str) -> Withdrawals:
    """
    회원 탈퇴 요청을 생성하는 비즈니스 로직을 처리.
    1. 탈퇴 처리 마감일(due_date)을 계산
    2. Withdrawals 모델 인스턴스를 생성하고 저장
    """
    # 비즈니스 로직 1: 탈퇴 처리 마감일은 14일 뒤로 설정
    due_date = date.today() + timedelta(days=14)

    # 비즈니스 로직 2: 모델 객체 생성(탈퇴 요청 생성)
    # withdrawal 모델에 탈퇴 요청 저장
    withdrawal = Withdrawals.objects.create(user=user, reason=reason, reason_detail=reason_detail, due_date=due_date)

    return withdrawal


def recover_account(email: str, verification_code: str) -> User | None:
    """
    인증 코드 검증 후 유저 계정을 복구하고 탈퇴 요청을 삭제.
    """

    # 탈퇴 요청한 유저 조회
    withdrawal = Withdrawals.objects.select_related("user").filter(user_email=email).first()

    # 탈퇴 요청이 없다면 Error 반환: 추후 오류 처리를 위한 ObjectDoesNotExist 예외 사용
    if not withdrawal:
        raise ObjectDoesNotExist("해당 이메일로 탈퇴 요청이 존재하지 않습니다.")

    # 유저 계정 복구 및 탈퇴 요청 삭제
    # 탈퇴 요청만 삭제하는 거고 user 모델의 상태는 변경하지 않음
    # 따라서 user.is_active = True를 명시적으로 설정
    user = withdrawal.user
    user.is_active = True
    user.save()
    # withdrawal.delete()

    return user
