from functools import wraps

from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.models import User


def jwt_required(view_func):
    """
    FBV에서 JWT AccessToken 검증 후 request.user 세팅
    """

    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse({"detail": "Authorization header missing"}, status=401)

        token_str = auth_header.split()[1]

        try:
            # 토큰 검증
            token = AccessToken(token_str)
            user_id = token["user_id"]
            user = User.objects.get(id=user_id)
            request.user = user
        except TokenError:
            return JsonResponse({"detail": "Invalid or expired token"}, status=401)
        except User.DoesNotExist:
            return JsonResponse({"detail": "User not found"}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapped