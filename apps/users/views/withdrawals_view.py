# apps/users/views/withdrawals_view.py

import logging

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models.withdrawals import Withdrawals
from apps.users.serializers.email_verification_serializers import (
    EmailVerifyCodeSerializer,
)
from apps.users.serializers.withdrawals_serializer import (
    WithdrawalRequestSerializer,
    WithdrawalResponseSerializer,
)
from apps.users.services.email_service import EmailVerificationService
from apps.users.services.exceptions import (
    EmailSendingFailedError,
    EmailVerificationCodeFailedError,
)
from apps.users.services.withdrawals_service import create_withdrawal, recover_account
from apps.users.utils.enums import VerificationPurpose

email_service = EmailVerificationService()
logger = logging.getLogger(__name__)


class WithdrawalAPIView(APIView):
    @extend_schema(
        summary="계정 탈퇴 요청",
        description="로그인한 사용자가 계정 탈퇴를 요청합니다. 성공 시 탈퇴 기록이 생성됩니다.",
        request=WithdrawalRequestSerializer,
        responses={
            200: WithdrawalResponseSerializer,
            401: OpenApiResponse(description="로그인이 필요합니다."),
            400: OpenApiResponse(description="잘못된 요청 데이터."),
        },
        examples=[
            OpenApiExample(
                "계정 탈퇴 요청 예시",
                value={"reason": "서비스 불만족"},
                request_only=True,
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        assert request.user.is_authenticated  # mypy 오류로 인한 검증 코드
        request_serializer = WithdrawalRequestSerializer(data=request.data, context={"request": request})
        request_serializer.is_valid(raise_exception=True)

        withdrawal_instance = create_withdrawal(**request_serializer.validated_data)

        response_serializer = WithdrawalResponseSerializer(instance=withdrawal_instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class AccountRecoveryAPIView(APIView):
    permission_classes = [AllowAny]
    """
    탈퇴 계정 복구 요청 API
    └ 이메일과 인증 코드 검증
    └ 복구 성공 시 계정 활성화 및 탈퇴 요청 삭제
    """

    @extend_schema(
        summary="탈퇴 계정 복구 요청",
        description="탈퇴 계정을 이메일 인증을 통해 복구합니다. 성공 시 계정이 활성화되고 탈퇴 기록은 삭제됩니다.",
        request=EmailVerifyCodeSerializer,
        responses={
            200: OpenApiResponse(description="계정 복구 성공"),
            400: OpenApiResponse(description="잘못된 인증 코드 또는 기타 요청 오류"),
            404: OpenApiResponse(description="탈퇴 요청이 존재하지 않음"),
            500: OpenApiResponse(description="이메일 발송 시스템 오류"),
        },
        examples=[
            OpenApiExample(
                "계정 복구 요청 예시",
                value={"email": "user@example.com", "verification_code": "123456"},
                request_only=True,
            )
        ],
    )
    def post(self, request: Request) -> Response:
        # 1) 유효성 검증
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2) 이 인증의 목적을 설정
        purpose = VerificationPurpose.RECOVER_ACCOUNT

        try:
            # 3) 인증 코드 검증
            email_service.verify_code(purpose, **serializer.validated_data)  # 검증 코드 호출

            # 4) 계정 복구
            recover_account(**serializer.validated_data)

            # 5) 성공 응답
            return Response({"detail": "계정이 복구되었습니다. 이제 로그인할 수 있습니다."}, status=status.HTTP_200_OK)

        # 6) 실패 응답
        # 6-1) 이메일 발송 시스템에 문제가 발생하였습니다.
        except EmailSendingFailedError as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 6-2) 이메일 인증 코드가 일치하지 않습니다.
        except EmailVerificationCodeFailedError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 6-3) 해당 이메일로 탈퇴 요청이 존재하지 않습니다.
        except Withdrawals.DoesNotExist as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception:
            logger.exception("계정 복구 처리 중 알 수 없는 오류 발생.")
            return Response({"detail": "알 수 없는 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
