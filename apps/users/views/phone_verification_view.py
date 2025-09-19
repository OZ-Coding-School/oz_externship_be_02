import logging

from django.core.cache import cache
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
from apps.users.services.phone_service import TwilioAuthService

twilio_service = TwilioAuthService()


class SendVerificationCodeAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PhoneVerificationSerializer
    authentication_classes = ()

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

    def post(self, request: Request) -> Response:
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            twilio_service.check_verification_code(**serializer.validated_data)
        except PhoneVerificationCodeFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "휴대폰 인증되었습니다"}, status=status.HTTP_200_OK)
