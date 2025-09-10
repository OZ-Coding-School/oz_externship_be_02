from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.withdrawals import (
    WithdrawalRequestSerializer,
    WithdrawalResponseSerializer,
)
from apps.users.services.withdrawals import create_withdrawal


class WithdrawalAPIView(APIView):
    def post(self, request: Request) -> Response:
        assert request.user.is_authenticated  # mypy 오류로 인한 검증 코드
        request_serializer = WithdrawalRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        withdrawal_instance = create_withdrawal(user=request.user, **request_serializer.validated_data)

        response_serializer = WithdrawalResponseSerializer(instance=withdrawal_instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
