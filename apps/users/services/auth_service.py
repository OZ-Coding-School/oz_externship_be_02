from typing import Optional, Union, cast

from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, Token

from apps.users.models import User


class AuthService:
    """
    이메일 로그인
    """

    @staticmethod
    def email_login(email: str, password: str) -> tuple[User, dict[str, str]]:
        # 유저 조회
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        # is_active 체크
        if user and not user.is_active:
            withdrawal = getattr(user, "withdrawal", None)
            raise AuthenticationFailed(
                detail={
                    "detail": "탈퇴 계정입니다. 복구 가능 기간 확인 바랍니다.",
                    "due_date": withdrawal.due_date if withdrawal else None,
                }
            )
        # 비밀번호 인증
        user: Union[User, None] = authenticate(email=email, password=password)
        if user is None:
            raise AuthenticationFailed("이메일 또는 비밀번호가 틀립니다")

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        tokens = {"access": access_token, "refresh": refresh_token}

        return user, tokens


class JWTService:
    @staticmethod
    def refresh_access_token(refresh_token: Optional[str]) -> str:
        """
        쿠키의 refresh 토큰으로 새로운 access 토큰 발급
        """
        refresh_token_str = cast(Token, refresh_token)
        if not refresh_token_str:
            raise AuthenticationFailed("재로그인이 필요합니다")
        try:
            token = RefreshToken(refresh_token_str)
            return str(token.access_token)
        except Exception as e:
            msg = str(e).lower()
            if "expired" in msg:
                raise AuthenticationFailed("리프레시 토큰이 만료되었습니다")
            raise AuthenticationFailed("유효하지 않은 토큰입니다")

    @staticmethod
    def revoke_refresh_tokens(refresh_token: Optional[str]) -> None:
        refresh_token_str = cast(Token, refresh_token)
        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
        except TokenError:
            raise AuthenticationFailed("리프레시 토큰이 유효하지 않습니다")
