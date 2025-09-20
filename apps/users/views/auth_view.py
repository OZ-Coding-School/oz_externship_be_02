from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.authentications import CookieJWTAuthentication
from apps.users.serializers.signup_serializers import UserSignupSerializer
from apps.users.services.exceptions import (
    EmailVerificationCodeFailedError,
    PhoneVerificationCodeFailedError,
)


class UserSignupAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request: Request) -> Response:
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "회원가입이 완료되었습니다", "user": serializer.data}, status=status.HTTP_201_CREATED
        )
