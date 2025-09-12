# apps/users/services/withdrawals.py

from datetime import date, timedelta

from apps.users.models.user import User
from apps.users.models.withdrawals import Withdrawals
from apps.users.services.email_service import EmailVerificationService


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
    # user.is_active는 views에서 처리(validate에서 처리하지 않는 이유: user가 비활성화된 상태일 수도 있기 때문) < 이거 자꾸 자동 완성되는데 뭐지
    withdrawal = Withdrawals.objects.create(user=user, reason=reason, reason_detail=reason_detail, due_date=due_date)

    return withdrawal


def recover_account(email: str, code: str) -> User | None:
    """
    인증 코드 검증 후 유저 계정을 복구하고 탈퇴 요청을 삭제.
    """

    # 탈퇴 요청한 유저 조회
    withdrawal = Withdrawals.objects.select_related("user").filter(user__email=email).first()

    # 탈퇴 요청이 없다면 None 반환
    if not withdrawal:
        return None

    user = withdrawal.user

    # 인증 코드 검증
    email_service = EmailVerificationService()
    verification_result = email_service.verify_code(email=email, code=code, purpose="recover_account")

    # 인증 코드가 유효하지 않다면 None 반환
    if verification_result.status_code != 200:
        return None

    # 유저 계정 복구 및 탈퇴 요청 삭제
    # 탈퇴 요청만 삭제하는 거고 user 모델의 상태는 변경하지 않음
    # 따라서 user.is_active = True를 명시적으로 설정
    user.is_active = True
    user.save()
    withdrawal.delete()

    return user
