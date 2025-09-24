import logging

from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.phone_verification_serializers import (
    PhoneVerificationSerializer,
    VerifyCodeSerializer,
)
from apps.users.services.exceptions import (
    PhoneSendingFailedError,
    PhoneVerificationCodeFailedError,
)
from apps.users.services.phone_service import (
    PhoneVerificationService,
    TwilioAuthService,
)

twilio_service = TwilioAuthService()
twilio_verified = PhoneVerificationService


class SendVerificationCodeAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PhoneVerificationSerializer
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="휴대폰 인증번호 전송",
        description="사용자가 입력한 휴대폰 번호로 인증번호를 전송합니다.",
        request=PhoneVerificationSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = PhoneVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            twilio_service.send_verification_code(phone_number=serializer.data["phone_number"])
        except PhoneSendingFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "휴대폰 인증번호가 전송되었습니다"}, status=status.HTTP_200_OK)


class VerifyCodeAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyCodeSerializer
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="휴대폰 인증번호 검증",
        description="사용자가 입력한 인증번호가 올바른지 확인합니다.",
        request=VerifyCodeSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            twilio_verified.is_verified(**serializer.validated_data)
        except PhoneVerificationCodeFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "휴대폰 인증되었습니다"}, status=status.HTTP_200_OK)
