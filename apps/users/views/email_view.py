from rest_framework import status
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
        result = email_service.send_verification_email(email, purpose)
        if "detail" in result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


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

        result = email_service.verify_code(email, purpose, verification_code)
        if "detail" in result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


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

        result = email_service.send_verification_email(email, purpose)
        if "detail" in result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


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

        result = email_service.verify_code(email, purpose, verification_code)
        if "detail" in result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


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
        if "detail" in result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


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

        result = email_service.verify_code(email, purpose, verification_code)
        if "detail" in result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
