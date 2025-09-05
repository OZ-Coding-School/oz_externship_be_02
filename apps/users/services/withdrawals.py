# apps/users/services/withdrawals.py

from datetime import date, timedelta
from apps.users.models.withdrawals import Withdrwals


# 사용자 정보와 탈퇴 대기 기간을 validated_data에 포함
def request_withdrawal(user, validated_data: dict) -> Withdrwals:
    validated_data["user"] = user
    validated_data["due_date"] = date.today() + timedelta(days=14)

    withdrawal = Withdrwals.objects.create(**validated_data)

    # 탈퇴 요청 즉시 계정을 비활성화할 것은 아니기 때문에 사용자의 active 상태는 확인하지 않음
    #! 문제: 탈퇴 대기 기간 동안 활동이 가능한 것인지?
    return withdrawal
