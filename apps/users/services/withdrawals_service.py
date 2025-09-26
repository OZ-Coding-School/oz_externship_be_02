# apps/users/services/withdrawals_service.py
from datetime import date, timedelta

from django.db import transaction
from moto.efs.exceptions import BadRequest

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

    # 비즈니스 로직 2: 모델 객체 생성(탈퇴 요청 생성) 후 withdrawal 모델에 탈퇴 요청 저장
    withdrawal = Withdrawals.objects.create(user=user, reason=reason, reason_detail=reason_detail, due_date=due_date)

    user.is_active = False
    user.save(update_fields=["is_active"])

    return withdrawal


def recover_account(email: str, verification_code: str) -> None:
    """
    인증 코드 검증 후 유저 계정을 복구하고 탈퇴 요청을 삭제.
    """

    # 1) 탈퇴 요청한 유저 조회: user(id)로 user의 email 찾기
    withdrawal = Withdrawals.objects.select_related("user").filter(user__email=email).first()

    # 1-1) 탈퇴 요청이 없다면 Error 반환: 추후 오류 처리를 위한 DoesNotExist 예외 사용
    if not withdrawal:
        raise Withdrawals.DoesNotExist("해당 이메일로 탈퇴 요청이 존재하지 않습니다.")

    if not withdrawal.user:
        raise BadRequest("이미 삭제 완료 처리된 계정입니다.")

    # 2) 유저 계정 복구와 탈퇴 요청 삭제: 탈퇴 요청만 삭제하는 거고 user 모델의 상태는 변경하지 않으므로 user.is_active = True를 명시적으로 설정
    with transaction.atomic():
        user = withdrawal.user
        user.is_active = True
        user.save()
        withdrawal.delete()
