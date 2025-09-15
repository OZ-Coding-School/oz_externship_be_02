from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsSuperUser(BasePermission):
    """
    요청을 보낸 유자가 is_superuser=True 인 경우에만 api 접근 허용
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_superuser)
