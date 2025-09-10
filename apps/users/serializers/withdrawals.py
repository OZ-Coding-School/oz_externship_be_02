from rest_framework import serializers

from apps.recruitments.serializers.recruitments_serializers import UserSerializer
from apps.users.models.withdrawals import Withdrawals


class WithdrawalRequestSerializer(serializers.ModelSerializer[Withdrawals]):

    class Meta:
        model = Withdrawals
        fields = ("reason", "reason_detail")


class WithdrawalResponseSerializer(serializers.ModelSerializer[Withdrawals]):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Withdrawals
        fields = ("user", "reason", "reason_detail", "due_date", "created_at", "updated_at")
