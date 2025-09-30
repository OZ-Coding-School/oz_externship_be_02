from django.db import IntegrityError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User, user
from apps.users.serializers.auth_serializers import (
    EmailLoginRequestSerializer,
    LoginResponseSerializer,
)
from apps.users.serializers.signup_serializers import UserSignupSerializer
from apps.users.services.auth_service import AuthService, JWTService


class UserSignupAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="회원가입",
        description="이메일/휴대폰 인증 후 회원가입을 진행합니다",
        request=UserSignupSerializer,
        responses={
            201: UserSignupSerializer,
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
            409: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "회원가입이 완료되었습니다", "user_": serializer.data}, status=status.HTTP_201_CREATED
        )


class EmailLoginAPIView(APIView):
    """
    이메일 로그인 + 토큰 발급
    """

    permission_classes = (AllowAny,)
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="이메일 로그인",
        description="이메일과 비밀번호로 로그인하여 액세스 토큰 발급",
        request=EmailLoginRequestSerializer,
        responses={
            200: OpenApiResponse(
                description="로그인 성공",
                response={
                    "type": "object",
                    "properties": {"access": {"type": "string", "example": "jwt.access.token.value"}},
                },
            ),
            401: OpenApiResponse(description="인증 실패"),
            400: OpenApiResponse(description="잘못된 요청"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = EmailLoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, tokens = AuthService.email_login(**serializer.validated_data)
        except AuthenticationFailed as e:
            if isinstance(e.detail, dict):
                return Response({"error": e.detail}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({"error": str(e.detail)}, status=status.HTTP_401_UNAUTHORIZED)

        user_data = LoginResponseSerializer(user).data
        # 유저 응답
        response = Response(
            {
                "user": user_data,
                "access_token": tokens["access"],
            },
            status=status.HTTP_200_OK,
        )

        response.set_cookie(
            "refresh_token", tokens["refresh"], httponly=True, domain=".ozcoding.site", secure=True, samesite="None"
        )

        return response


class LogoutAPIView(APIView):
    """
    로그아웃: Refresh  토큰 블랙리스트 처리
    """

    permission_classes = (AllowAny,)
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="로그아웃",
        description="쿠키에 저장된 리프레시 토큰을 사용하여 로그아웃 처리",
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
            401: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
    )
    def post(self, request: Request) -> Response:
        refresh = request.COOKIES.get("refresh_token")

        if not refresh:
            return Response({"error": "refresh 토큰이 필요합니다"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            JWTService.revoke_refresh_tokens(refresh)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status.HTTP_401_UNAUTHORIZED)

        response = Response({"detail": "로그아웃이 완료되었습니다"}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        return response


class CookieTokenRefreshAPIView(APIView):
    """
    refresh 쿠키를 이용한 access 토큰 재발급
    """

    permission_classes = (AllowAny,)
    authentication_classes = ()

    @extend_schema(
        tags=["auth"],
        summary="액세스토큰 재발급",
        description="쿠키에 있는 리프레시 토큰으로 액세스토큰 재발급",
        responses={
            200: OpenApiResponse(
                description="토큰 재발급 성공",
                response={
                    "type": "object",
                    "properties": {"access": {"type": "string", "example": "jwt.new.access.token"}},
                },
            ),
            401: OpenApiResponse(description="인증 실패"),
            400: OpenApiResponse(description="잘못된 요청"),
        },
    )
    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get("refresh_token")

        try:
            access_token = JWTService.refresh_access_token(refresh_token)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status.HTTP_401_UNAUTHORIZED)
        except ValidationError as e:
            return Response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)

        return Response({"access": access_token}, status=status.HTTP_200_OK)
