from typing import Dict, AnyStr, Any

from rest_framework_simplejwt.tokens import RefreshToken, TokenError

# 공통 토큰 발급 함수
def genarate_tokens_for_user(user) -> Dict[str, str]:
    """
   로그인 인증 완료 후 access + refresh 토큰 발급
    """
    refresh = RefreshToken.for_user(user)
    return {
        "access" : str(refresh.access_token),
        "refresh" : str(refresh),
    }


def refresh_access_token(refresh_token: str)-> Dict[str, str]:
    """
    액세스토큰 재발급
    """
    try:
        token = RefreshToken(refresh_token)
        return {
            "access" : str(token.access_token),
            "refresh" : str(token),
        }
    except TokenError:
        raise ValueError("Refresh token is invalid or expired")