from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.email_verification_serializers import (
    EmailVerificationRequestSerializer,
    EmailVerifyCodeSerializer,
)
from apps.users.services.email_service import EmailVerificationService
from apps.users.utils.enums import VerificationPurpose


class SignUpEmailVerificationSendAPIView(APIView):
    permission_classes = (AllowAny,)
    """
    회원가입 이메일 코드 전송
    """

    def post(self, request: Request) -> Response:
        serializer = EmailVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = VerificationPurpose.SIGNUP

        return EmailVerificationService().send_verification_email(email=email, purpose=purpose)


class SignUpEmailVerifiCationVerifyAPIView(APIView):
    permission_classes = [AllowAny]
    """
    회원가입 이메일 전송 코드 검증
    """

    def post(self, request: Request) -> Response:
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = VerificationPurpose.SIGNUP
        verification_code = serializer.validated_data["verification_code"]

        return EmailVerificationService().verify_code(email=email, purpose=purpose, verification_code=verification_code)


class PasswordResetEmailVerificationSendAPIView(APIView):
    permission_classes = [AllowAny]
    """
    비밀번호 찾기 이메일 코드 전송 
    """

    def post(self, request: Request) -> Response:
        serializer = EmailVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = VerificationPurpose.RESET_PASSWORD

        return EmailVerificationService().send_verification_email(email=email, purpose=purpose)


class PassowrdResetEmailVerificationVerifyAPIView(APIView):
    permission_classes = [AllowAny]
    """
    비밀번호 찾기 이메일 전송 코드 검증
    """

    def post(self, request: Request) -> Response:
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = VerificationPurpose.RESET_PASSWORD
        verification_code = serializer.validated_data["verification_code"]

        return EmailVerificationService().verify_code(email=email, purpose=purpose, verification_code=verification_code)


class AccountRecoveryEmailVerificationSendAPIView(APIView):
    permission_classes = [AllowAny]
    """
    계정 복구 이메일  코드 전송
    """

    def post(self, request: Request) -> Response:
        serializer = EmailVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = VerificationPurpose.RECOVER_ACCOUNT

        return EmailVerificationService().send_verification_email(email=email, purpose=purpose )


class AccountRecoveryEmailVerificationVerifyAPIView(APIView):
    permission_classes = [AllowAny]
    """
    계정 복구 이메일 코드 검증
    """

    def post(self, request: Request) -> Response:
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        purpose = VerificationPurpose.RECOVER_ACCOUNT
        verification_code = serializer.validated_data["verification_code"]

        return EmailVerificationService().verify_code(email=email, purpose=purpose, verification_code=verification_code)
