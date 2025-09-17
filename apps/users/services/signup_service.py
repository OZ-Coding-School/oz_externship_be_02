from apps.users.models import User
from apps.users.services.email_service import EmailVerificationService
from apps.users.services.exceptions import (
    EmailVerificationCodeFailedError,
    PhoneVerificationCodeFailedError,
)
from apps.users.services.phone_service import TwilioAuthService
from apps.users.utils.enums import VerificationPurpose

twilio_service = TwilioAuthService()
email_service = EmailVerificationService()


class UserSignUpService:
    @staticmethod
    def signup(
        *,
        email: str,
        password: str,
        nickname: str,
        name: str,
        phone_number: str,
        birthday: str,
        gender: str,
    ) -> User:
        """
        회원가입 로직
        """

        user = User(
            email=email,
            nickname=nickname,
            name=name,
            phone_number=phone_number,
            birthday=birthday,
            gender=gender,
        )
        user.set_password(password)
        user.save()

        return user
