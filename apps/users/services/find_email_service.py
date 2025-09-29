# apps/users/services/find_email_service.py

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, ValidationError

from apps.users.models.user import User
from apps.users.services.exceptions import PhoneSendingFailedError
from apps.users.services.phone_service import TwilioAuthService
from apps.users.utils.enums import VerificationPurpose

phone_service = TwilioAuthService()


class PhoneVerificationService:
    @staticmethod
    def send_phone_code(phone_number: str) -> None:
        """
        휴대폰 번호로 인증 번호를 전송.
        """
        if not phone_number:
            raise ValidationError("휴대폰 번호를 입력해주세요.")

        purpose = VerificationPurpose.FIND_EMAIL
        try:
            phone_service.send_verification_code(phone_number, purpose)
        except PhoneSendingFailedError as e:
            # 서비스 예외를 DRF ValidationError로 변환
            raise ValidationError(f"휴대폰 인증 번호 전송에 실패했습니다: {str(e)}")
