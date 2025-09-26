from typing import Any, ClassVar, Dict

from django.urls import reverse

from apps.users.models.user import User
from apps.users.services.email_service import EmailVerificationService
from apps.users.services.phone_service import PhoneVerificationService


class TestUserMixin:

    @staticmethod
    def _create_test_user(**kwargs: Any) -> User:
        default = {
            "email": "test@email.com",
            "password": "testpassword",
            "name": "테스트유저",
            "nickname": "tester",
            "phone_number": "01012345678",
            "gender": "M",
            "birthday": "2000-01-01",
        }
        default.update(kwargs)
        return User.objects.create_user(**default)

    @staticmethod
    def get_email_recover_account_urls() -> Dict[str, str]:
        """계정 복구에 필요한 이메일과 URL들을 반환합니다."""
        return {
            "send_url": reverse("recover_account_send"),
            "verify_url": reverse("recover_account_verify"),
        }

    @staticmethod
    def get_password_reset_urls() -> Dict[str, str]:
        """비밀번호 재설정에 필요한 이메일과 URL들을 반환합니다."""
        return {
            "send_url": reverse("password_reset_send"),
            "verify_url": reverse("password_reset_verify"),
        }

    @staticmethod
    def get_email_verification_urls() -> Dict[str, str]:
        """이메일 인증에 필요한 이메일과 URL들을 반환합니다."""
        return {
            "send_url": reverse("email_send_code"),
            "verify_url": reverse("email_verify_code"),
        }

    @staticmethod
    def get_phone_verification_urls() -> Dict[str, str]:
        """휴대폰 인증에 필요한 URL들을 반환합니다."""
        return {
            "send_url": reverse("phone_send_code"),
            "verify_url": reverse("phone_verify_code"),
        }


class VerificationMixin(TestUserMixin):
    test_email: ClassVar[str]
    send_url: ClassVar[str]
    verify_url: ClassVar[str]
    user: ClassVar[User]
    phone_number: ClassVar[str]
    verification_code: ClassVar[str]
    signup_data: ClassVar[dict[str, Any]]
    url: ClassVar[str]
    email: ClassVar[str]
    password: ClassVar[str]
    login_url: ClassVar[str]
    refresh_url: ClassVar[str]
    revoke_url: ClassVar[str]
    email_service: ClassVar[EmailVerificationService]
    phone_service: ClassVar[PhoneVerificationService]
