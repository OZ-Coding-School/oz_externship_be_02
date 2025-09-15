from enum import Enum
from typing import Literal

from django.db import transaction

from apps.users.models import User

PermissionType = Literal["admin", "staff", "general"]


class PermissionLevel(Enum):
    ADMIN = (True, True)
    STAFF = (True, False)
    GENERAL = (False, False)


class UserPermissionService:
    @staticmethod
    @transaction.atomic
    def update_user_permission(user: User, permission: PermissionType) -> User:
        try:
            permission_setting = PermissionLevel[permission.upper()].value
        except KeyError:
            permission_setting = PermissionLevel.GENERAL.value

        user.is_staff, user.is_superuser = permission_setting

        user.save(update_fields=["is_superuser", "is_staff", "updated_at"])
        return user
