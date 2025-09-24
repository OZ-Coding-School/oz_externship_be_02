from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class AdminOnly(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False
        return bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
