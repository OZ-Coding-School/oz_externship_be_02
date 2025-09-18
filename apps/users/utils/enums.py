import enum

from rest_framework.exceptions import ValidationError


class VerificationPurpose(enum.StrEnum):
    SIGNUP = "signup"  # 회원가입
    RESET_PASSWORD = "reset_password"  # 비밀번호 찾기
    RECOVER_ACCOUNT = "recover_account"  # 계정복구
    PROFILE_UPDATE = "profile_update"  # 회원정보 수정
    FIND_EMAIL = "find_email"  # 이메일 찾기


def validate_purpose(purpose: str) -> str:
    """
    purpose를 넘겨받아서 VerificationPurpose 해당하는지 검증하는 함수
    """
    if purpose not in VerificationPurpose:
        raise ValidationError(f"Purpose {purpose} is not valid")
    return purpose


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
