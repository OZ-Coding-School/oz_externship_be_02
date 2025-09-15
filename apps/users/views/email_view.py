from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
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

email_service = EmailVerificationService()


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

        email_service.send_verification_email(email, purpose)
        return Response({"detail": "인증에 성공했습니다"}, status=status.HTTP_200_OK)


class SignUpEmailVerifiCationVerifyAPIView(APIView):
    permission_classes = (AllowAny,)
    """
    회원가입 이메일 전송 코드 검증
    """

    def post(self, request: Request) -> Response:
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        purpose = VerificationPurpose.SIGNUP

        if not email_service.verify_code(purpose, **serializer.validated_data):
            return Response({"error": "인증번호가 일치하지 않습니다"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "인증이 완료되었습니다"}, status=status.HTTP_200_OK)


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

        email_service.send_verification_email(email, purpose)
        return Response({"detail": "인증에 완료되었습니다"}, status=status.HTTP_200_OK)


class PassowrdResetEmailVerificationVerifyAPIView(APIView):
    permission_classes = [AllowAny]
    """
    비밀번호 찾기 이메일 전송 코드 검증
    """

    def post(self, request: Request) -> Response:
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        purpose = VerificationPurpose.RESET_PASSWORD

        email_service.verify_code(purpose=purpose, **serializer.validated_data)
        return Response({"detail": "인증에 성공했습니다"}, status=status.HTTP_200_OK)


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

        result = email_service.send_verification_email(email, purpose)
        if not result:
            return Response({"error": "전송에 실패했습니다"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "인증 번호를 전송했습니다"}, status=status.HTTP_200_OK)


class AccountRecoveryEmailVerificationVerifyAPIView(APIView):
    permission_classes = [AllowAny]
    """
    계정 복구 이메일 코드 검증
    """

    def post(self, request: Request) -> Response:
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        purpose = VerificationPurpose.RECOVER_ACCOUNT

        result = email_service.verify_code(purpose=purpose, **serializer.validated_data)
        if not result:
            return Response({"error": "인증번호가 일치하지 않습니다"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "인증에 성공했습니다"}, status=status.HTTP_200_OK)
