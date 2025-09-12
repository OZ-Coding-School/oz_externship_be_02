# apps/users/views/withdrawals.py

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.withdrawals import (
    AccountRecoverySerializer,
    WithdrawalRequestSerializer,
    WithdrawalResponseSerializer,
)
from apps.users.services.withdrawals import create_withdrawal, recover_account


class WithdrawalAPIView(APIView):
    def post(self, request: Request) -> Response:
        assert request.user.is_authenticated  # mypy 오류로 인한 검증 코드
        request_serializer = WithdrawalRequestSerializer(data=request.data, context={"request": request})
        request_serializer.is_valid(raise_exception=True)

        withdrawal_instance = create_withdrawal(**request_serializer.validated_data)

        response_serializer = WithdrawalResponseSerializer(instance=withdrawal_instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class AccountRecoveryAPIView(APIView):
    """
    탈퇴 계정 복구 요청 API
    - 이메일과 인증 코드 검증
    - 복구 성공 시 계정 활성화 및 탈퇴 요청 삭제
    - 복구 실패 시 에러 응답 반환
    """

    def post(self, request: Request) -> Response:
        serializer = AccountRecoverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        user = recover_account(email=email, code=code)
        if not user:
            return Response({"error": "계정 복구에 실패했습니다."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "계정이 복구되었습니다. 이제 로그인할 수 있습니다."}, status=status.HTTP_200_OK)
