from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.phone_verification_serializers import (
    PhoneVerificationSerializer,
    VerifyCodeSerializer,
)
from apps.users.services.phone_service import TwilioAuthService

twilio_service = TwilioAuthService()


class SendVerificationCodeAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PhoneVerificationSerializer

    def post(self, request: Request) -> Response:
        serializer = PhoneVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]

        result = twilio_service.send_verification_code(phone_number)
        if result.get("success"):
            return Response({"detail": "인증번호가 전송되었습니다"}, status=status.HTTP_200_OK)
        return Response({"error": "인증번호 전송에 실패했습니다"}, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyCodeSerializer

    def post(self, request: Request) -> Response:
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        code = serializer.validated_data["verification_code"]

        result = twilio_service.check_verification_code(phone_number, code)
        if result.get("success"):
            return Response({"detail": "인증되었습니다"}, status=status.HTTP_200_OK)
        return Response({"error": "인증번호가 일치하지 않습니다"}, status=status.HTTP_400_BAD_REQUEST)
