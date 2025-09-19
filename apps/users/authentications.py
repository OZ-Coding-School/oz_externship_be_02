from typing import Optional, Tuple

from django.contrib.auth.base_user import AbstractBaseUser
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken, Token

from apps.users.models import User


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request: Request) ->  Optional[Tuple["User", Token]]: #type: ignore[override]
        access_token = request.COOKIES.get("access")

        if not access_token:
            raise AuthenticationFailed("로그인이 필요합니다.")

        request.META["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
        try:
            return super().authenticate(request) #type: ignore
        except InvalidToken as e:
            # 예외 메시지를 확인하여 만료 여부를 정확히 판단
            if "expired" in str(e).lower():
                raise AuthenticationFailed("토큰이 만료되었습니다.")
            else:
                raise AuthenticationFailed("유효하지 않은 토큰입니다.")
        except TokenError:
            raise AuthenticationFailed("토큰 처리 중 오류가 발생했습니다.")
