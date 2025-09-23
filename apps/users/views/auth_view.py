from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.auth_serializers import EmailLoginSerializer
from apps.users.serializers.signup_serializers import UserSignupSerializer
from apps.users.services.auth_service import AuthService, JWTService


class UserSignupAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request: Request) -> Response:
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "회원가입이 완료되었습니다", "user_": serializer.data}, status=status.HTTP_201_CREATED
        )




class EmailLoginAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    """
    이메일 로그인 + 토큰 발급
    """

    def post(self, request: Request) -> Response:
        serializer = EmailLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tokens = AuthService.email_login(**serializer.validated_data)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        response = Response({"access": tokens["access"]}, status=status.HTTP_200_OK)

        response.set_cookie(
            "refresh", tokens["refresh"], httponly=True, domain=".ozcoding.site", secure=True, samesite="None"
        )

        return response


class LogoutAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    """
    로그아웃: Refresh  토큰 블랙리스트 처리
    """

    def post(self, request: Request) -> Response:
        refresh = request.COOKIES.get("refresh")

        if not refresh:
            return Response({"error": "refresh 토큰이 필요합니다"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            JWTService.revoke_refresh_tokens(refresh)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status.HTTP_401_UNAUTHORIZED)

        response = Response({"detail": "로그아웃이 완료되었습니다"}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh")
        return response


class CookieTokenRefreshAPIView(APIView):
    """
    refresh 쿠키를 이용한 access 토큰 재발급
    """

    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get("refresh")

        try:
            access_token = JWTService.refresh_access_token(refresh_token)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status.HTTP_401_UNAUTHORIZED)
        except ValidationError as e:
            return Response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)

        return Response({"access": access_token}, status=status.HTTP_200_OK)
