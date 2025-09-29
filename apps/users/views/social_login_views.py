from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.social_login_serializers import (
    SocialLoginCallbackRequestSerializer,
)
from apps.users.services.kakao_login_service import KakaoService


class KakaoLoginCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SocialLoginCallbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = KakaoService.kakao_login(serializer.validated_data["code"])
        rt = tokens.pop("refresh_token")
        response = Response(data=tokens, status=status.HTTP_200_OK)
        response.set_cookie("refresh_token", rt, httponly=True, domain=".ozcoding.site", samesite="None", secure=True)
        return response
