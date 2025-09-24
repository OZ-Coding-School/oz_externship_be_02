from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.email_verification_serializers import (
    EmailVerificationRequestSerializer,
    EmailVerifyCodeSerializer,
)
from apps.users.services.email_service import EmailVerificationService
from apps.users.services.exceptions import (
    EmailSendingFailedError,
    EmailVerificationCodeFailedError,
)
from apps.users.utils.enums import VerificationPurpose

email_service = EmailVerificationService()


class SignUpEmailVerificationSendAPIView(APIView):
    """
    회원가입 이메일 코드 전송
    """

    permission_classes = (AllowAny,)
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="이메일 인증 요청",
        description="회원가입을 하기위해 이메일 인증 코드 발송",
        request=EmailVerificationRequestSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = EmailVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        purpose = VerificationPurpose.SIGNUP
        try:
            email_service.send_verification_email(serializer.validated_data["email"], purpose)
        except EmailSendingFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "인증 번호를 전송했습니다"}, status=status.HTTP_200_OK)


class SignUpEmailVerifiCationVerifyAPIView(APIView):
    """
    회원가입 이메일 전송 코드 검증
    """

    permission_classes = (AllowAny,)
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="이메일 검증 요청",
        description="회원가입을 하기 위해 이메일 인증 코드 검증",
        request=EmailVerifyCodeSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        purpose = VerificationPurpose.SIGNUP
        try:
            email_service.verify_code(purpose, **serializer.validated_data)
        except EmailVerificationCodeFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "인증이 완료되었습니다"}, status=status.HTTP_200_OK)


class PasswordResetEmailVerificationSendAPIView(APIView):
    """
    비밀번호 찾기 이메일 코드 전송
    """

    permission_classes = [AllowAny]
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="이메일 인증 요청",
        description="비밀번호를 찾기 위해 이메일 인증 코드 발송",
        request=EmailVerificationRequestSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = EmailVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = VerificationPurpose.RESET_PASSWORD

        if not User.objects.filter(email=email).exists():
            return Response({"error": "해당 이메일로 가입된 계정이 없습니다"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            email_service.send_verification_email(email, purpose)
        except EmailSendingFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "인증번호를 전송했습니다"}, status=status.HTTP_200_OK)


class PassowrdResetEmailVerificationVerifyAPIView(APIView):
    """
    비밀번호 찾기 이메일 전송 코드 검증
    """

    permission_classes = [AllowAny]
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="이메일 검증 요청",
        description="비밀번호를 찾기 위해 이메일 인증 코드 검증",
        request=EmailVerifyCodeSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        purpose = VerificationPurpose.RESET_PASSWORD
        try:
            email_service.verify_code(purpose=purpose, **serializer.validated_data)
        except EmailVerificationCodeFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "인증에 성공했습니다"}, status=status.HTTP_200_OK)


class AccountRecoveryEmailVerificationSendAPIView(APIView):
    """
    계정 복구 이메일 코드 전송
    """

    permission_classes = [AllowAny]
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="이메일 인증 요청",
        description="계정복구를 하기 위해 이메일 인증 코드 발송",
        request=EmailVerificationRequestSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = EmailVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = VerificationPurpose.RECOVER_ACCOUNT

        if not User.objects.filter(email=email).exists():
            return Response({"error": "해당 이메일로 가입된 계정이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            email_service.send_verification_email(email, purpose)
        except EmailSendingFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "인증 번호를 전송했습니다"}, status=status.HTTP_200_OK)


class AccountRecoveryEmailVerificationVerifyAPIView(APIView):
    """
    계정 복구 이메일 코드 검증
    """

    permission_classes = [AllowAny]
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="이메일 검증 요청",
        description="계정복구를 하기 위해 이메일 인증 코드 검증",
        request=EmailVerifyCodeSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        purpose = VerificationPurpose.RECOVER_ACCOUNT
        try:
            email_service.verify_code(purpose=purpose, **serializer.validated_data)
        except EmailVerificationCodeFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "인증에 성공했습니다"}, status=status.HTTP_200_OK)
