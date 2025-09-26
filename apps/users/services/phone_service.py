from typing import Any, Dict

from django.conf import settings
from django.core.cache import cache
from twilio.base.exceptions import TwilioRestException  # type: ignore
from twilio.rest import Client  # type: ignore

from apps.users.services.exceptions import (
    PhoneSendingFailedError,
    PhoneVerificationCodeFailedError,
)
from apps.users.utils.enums import VerificationPurpose


class TwilioAuthService:
    def __init__(self) -> None:
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.service_sid = settings.TWILIO_VERIFY_SERVICE_SID
        self.verify_service = self.client.verify.v2.services(self.service_sid)

    # 인증번호 전송
    def send_verification_code(self, phone_number: str, purpose: VerificationPurpose) -> None:
        try:
            self.client.verify.v2.services(self.service_sid).verifications.create(to=phone_number, channel="sms")
        except TwilioRestException as e:
            raise PhoneSendingFailedError(f"휴대폰 인증번호 발송 실패 {e}")

    # 인증번호 검증

    def check_verification_code(self, phone_number: str, verification_code: str, purpose: VerificationPurpose) -> None:
        try:
            response = self.verify_service.verification_checks.create(to=phone_number, code=verification_code)
        except TwilioRestException as e:
            raise PhoneVerificationCodeFailedError(f"휴대폰 인증에 실패했습니다 {e}")
        if response.status != "approved":
            raise PhoneVerificationCodeFailedError("휴대폰 인증번호가 일치하지 않습니다")

        verified_key = f"{purpose.value}-verified-{phone_number}"
        cache.set(verified_key, verification_code, timeout=600)


class PhoneVerificationService:
    @staticmethod
    def is_verified(phone_number: str, verification_code: str, purpose: VerificationPurpose) -> bool:
        """
        번호 + 코드 검증 완료 상태 확인
        """
        verified_key = f"{purpose.value}-verified-{phone_number}"
        return bool(str(cache.get(verified_key)) == verification_code)
