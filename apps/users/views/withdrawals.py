# apps/users/views/withdrawals.py

from typing import cast

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models.user import User
from apps.users.serializers.withdrawals import WithdrawalRequestSerializer
from apps.users.services.withdrawals import withdrawal_user


# ---------- 탈퇴 신청 ----------
class WithdrawalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = WithdrawalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = cast(User, self.request.user)
        reason = serializer.validated_data["reason"]
        reason_detail = serializer.validated_data["reason_detail"]

        return withdrawal_user(user=user, reason=reason, reason_detail=reason_detail)
