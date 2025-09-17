from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.signup_serializers import UserSignupSerializer
from apps.users.services.exceptions import (
    EmailVerificationCodeFailedError,
    PhoneVerificationCodeFailedError,
)
from apps.users.services.signup_service import UserSignUpService


class UserSignupAPIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        signup_data = serializer.validated_data.copy()
        signup_data.pop("email_verification_code", None)
        signup_data.pop("phone_verification_code", None)

        try:
            user = UserSignUpService.signup(**signup_data)
        except EmailVerificationCodeFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PhoneVerificationCodeFailedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "회원가입이 완료되었습니다", "user_id": user.uuid}, status=status.HTTP_201_CREATED)
