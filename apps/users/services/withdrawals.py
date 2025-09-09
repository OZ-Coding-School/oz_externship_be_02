# apps/users/services/withdrawals.py

from datetime import date, timedelta

from rest_framework import status
from rest_framework.response import Response

from apps.users.models.social_user import SocialUser
from apps.users.models.user import User
from apps.users.models.withdrawals import Withdrawals, WithdrawalsReasonChoices


# ---------- 탈퇴 신청(일반/소셜 구분) ----------
def withdrawal_user(user: User, reason: str, reason_detail: str) -> Response:
    if Withdrawals.objects.filter(user=user).exists():
        return Response({"error": "이미 탈퇴 요청이 존재합니다."}, status=status.HTTP_400_BAD_REQUEST)

    due_date = date.today() + timedelta(days=14)
    withdrawal = Withdrawals.objects.create(user=user, reason=reason, reason_detail=reason_detail, due_date=due_date)

    # 탈퇴 신청 즉시 비활성화 -> 저장
    user.is_active = False
    user.save()

    return Response(
        data={"detail": "회원 탈퇴가 완료되었습니다. 계정은 14일 후에 삭제됩니다."}, status=status.HTTP_200_OK
    )
