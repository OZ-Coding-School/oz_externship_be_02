from enum import Enum

from apps.users.models import User


class Permission(Enum):
    ADMIN = ("admin", "관리자")
    STAFF = ("staff", "스태프")
    GENERAL = ("general", "일반회원")

    @classmethod
    def from_user(cls, user: User) -> "Permission":
        """User 객체의 is_superuser, is_staff를 확인해 해당하는 Enum을 반환"""
        if user.is_superuser:
            return cls.ADMIN
        if user.is_staff:
            return cls.STAFF
        return cls.GENERAL


class UserStatus(Enum):
    ACTIVE = ("active", "활성화")
    INACTIVE = ("inactive", "비활성화")
    WITHDRAWN = ("withdrawn", "탈퇴 진행중")
