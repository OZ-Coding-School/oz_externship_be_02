# apps/users/serializers/withdrawals.py

from typing import Any, Dict

from rest_framework import serializers

from apps.recruitments.serializers.recruitments_serializers import UserSerializer
from apps.users.models.withdrawals import Withdrawals


class WithdrawalRequestSerializer(serializers.ModelSerializer[Withdrawals]):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Withdrawals
        fields = ("user", "reason", "reason_detail")

    # user는 validated_data에 자동으로 포함됨
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        user = data["user"]
        if not self.instance and Withdrawals.objects.filter(user=user).exists():
            raise serializers.ValidationError(code="error", detail="이미 탈퇴 요청이 존재합니다.")
        return data


class WithdrawalResponseSerializer(serializers.ModelSerializer[Withdrawals]):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Withdrawals
        fields = ("user", "reason", "reason_detail", "due_date", "created_at", "updated_at")


class AccountRecoverySerializer(serializers.Serializer[Withdrawals]):
    # 복구 코드 입력 검증용
    # email 정의 안 하는 이유: request.user.email을 그대로 쓰는 게 Django가 권장하는 방식으로 보임
    code = serializers.CharField()
