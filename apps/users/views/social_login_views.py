from rest_framework import status
from rest_framework.exceptions import APIException, ParseError, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.logger import logger
from apps.users.serializers.social_login_serializers import (
    SocialLoginCallbackRequestSerializer,
)
from apps.users.services.kakao_login_service import KakaoService
from apps.users.services.naver_login_service import NaverService


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


class NaverLoginCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SocialLoginCallbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tokens = NaverService.naver_login(serializer.validated_data["code"])
        except (ValidationError, ParseError, APIException) as e:
            logger.warning("NAVER_LOGIN_FAIL %s", getattr(e, "detail", str(e)))
            raise

        rt = tokens.pop("refresh_token")
        response = Response(data=tokens, status=status.HTTP_200_OK)
        response.set_cookie("refresh_token", rt, httponly=True, domain=".ozcoding.site", samesite="None", secure=True)
        return response
