from typing import Dict, Optional, Tuple

from django.contrib.auth import authenticate, get_user_model
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from apps.users.models import User


class AuthService:
    """
    이메일 로그인
    """

    @staticmethod
    def email_login(email: str, password: str) -> Tuple[str, str]:
        user = authenticate(email=email, password=password)

        if not user:
            raise AuthenticationFailed("이메일 또는 비밀번호가 틀립니다")
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        return access_token, refresh_token

    @staticmethod
    def revoke_refresh_tokens(refresh_token: Optional[str]) -> None:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            raise ValidationError("리프레시 토큰이 유효하지 않습니다")


class JWTService:
    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        쿠키의 refresh 토큰으로 새로운 access 토큰 발급
        """
        if not refresh_token:
            raise AuthenticationFailed("재로그인이 필요합니다")
        try:
            token = RefreshToken(refresh_token)
            return str(token.access_token)
        except Exception as e:
            msg = str(e).lower()
            if "expired" in msg:
                raise AuthenticationFailed("리프레시 토큰이 만료되었습니다")
            raise AuthenticationFailed("유효하지 않은 토큰입니다")
