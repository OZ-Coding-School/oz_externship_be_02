from dataclasses import dataclass
from enum import Enum
from typing import Literal

from django.db import transaction

from apps.users.models import User

PermissionType = Literal["admin", "staff", "general"]


@dataclass(frozen=True)
class PermissionConfig:
    is_staff: bool
    is_superuser: bool


class PermissionLevel(Enum):
    ADMIN = PermissionConfig(is_staff=True, is_superuser=True)
    STAFF = PermissionConfig(is_staff=True, is_superuser=False)
    GENERAL = PermissionConfig(is_staff=False, is_superuser=False)


PERMISSION_MAP = {
    "admin": PermissionLevel.ADMIN,
    "staff": PermissionLevel.STAFF,
    "general": PermissionLevel.GENERAL,
}


class UserPermissionService:
    @staticmethod
    @transaction.atomic
    def update_user_permission(user: User, permission: PermissionType) -> User:
        permission_level = PERMISSION_MAP.get(permission, PermissionLevel.GENERAL)
        config: PermissionConfig = permission_level.value

        user.is_staff = config.is_staff
        user.is_superuser = config.is_superuser

        user.save(update_fields=["is_superuser", "is_staff", "updated_at"])
        return user
