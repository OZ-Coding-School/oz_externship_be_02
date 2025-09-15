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
