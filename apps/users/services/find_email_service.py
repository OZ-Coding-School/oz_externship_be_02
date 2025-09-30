# apps/users/services/find_email_service.py

from rest_framework.exceptions import NotFound

from apps.users.models.user import User
from apps.users.services.phone_service import (  # type: ignore
    PhoneSendingFailedError,
    PhoneVerificationCodeFailedError,
    PhoneVerificationService,
    TwilioAuthService,
)
from apps.users.utils.enums import VerificationPurpose

phone_service = TwilioAuthService()


class FindEmailPhoneVerificationService:
    @staticmethod
    def send_code_for_find_email(phone_number: str, purpose: VerificationPurpose) -> None:
        """
        휴대폰 인증 코드 전송
        """
        try:
            phone_service.send_verification_code(phone_number, purpose)
        except PhoneSendingFailedError as e:
            raise PhoneSendingFailedError("휴대폰 인증 번호 전송에 실패했습니다.") from e

    @staticmethod
    def verify_code(phone_number: str, verification_code: str, purpose: VerificationPurpose) -> None:
        """
        휴대폰 인증 코드 검증
        """
        if not PhoneVerificationService.is_verified(
            phone_number=phone_number, verification_code=verification_code, purpose=purpose
        ):
            raise PhoneVerificationCodeFailedError("인증 정보가 일치하지 않습니다.")


class FindEmailService:
    @staticmethod
    def find_email(name: str, phone_number: str) -> str:
        """
        이름과 (인증된) 휴대폰 번호로 사용자 이메일 조회
        """
        try:
            user = User.objects.get(name=name, phone_number=phone_number)
        except User.DoesNotExist:
            raise NotFound("사용자를 찾을 수 없습니다.")  # 404 처리용 예외

        return user.email
