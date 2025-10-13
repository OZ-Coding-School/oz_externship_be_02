# oz_externship_be/apps/chat/middleware.py
import logging
from typing import Any, Callable, Coroutine, Dict, Union
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()
logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token_string: str) -> Union[AbstractBaseUser, AnonymousUser]:
    """
    전달된 액세스 토큰 문자열을 검증하고, 유효할 경우 사용자 객체를 반환
    """
    try:
        access_token = AccessToken(token_string)  # type: ignore

        user_id = access_token.get(api_settings.USER_ID_CLAIM)

        if user_id is None:
            return AnonymousUser()

        return User.objects.get(id=user_id)

    except (InvalidToken, TokenError) as e:
        logger.warning(f"WebSocket: Invalid token received - {e}")
        return AnonymousUser()
    except User.DoesNotExist:
        user_id_for_log = locals().get("user_id", "unknown")
        logger.warning(f"WebSocket: User not found for token with user_id: {user_id_for_log}")
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    WebSocket 연결 시 쿼리 파라미터로 전달된 JWT를 인증하는 Channels 미들웨어
    """

    def __init__(self, app: Callable[..., Any]):
        self.app = app

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Coroutine[Any, Any, Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> Any:
        query_params = parse_qs(scope.get("query_string", b"").decode("utf-8"))
        token = query_params.get("token", [None])[0]

        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)
