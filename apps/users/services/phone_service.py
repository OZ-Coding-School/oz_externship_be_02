from typing import Any, Dict

from django.conf import settings
from django.core.cache import cache
from twilio.base.exceptions import TwilioRestException  # type: ignore
from twilio.rest import Client  # type: ignore

from apps.users.services.exceptions import (
    PhoneSendingFailedError,
    PhoneVerificationCodeFailedError,
)


class TwilioAuthService:
    def __init__(self) -> None:
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.service_sid = settings.TWILIO_VERIFY_SERVICE_SID

    # 인증번호 전송
    def send_verification_code(self, phone_number: str) -> None:
        try:
            self.client.verify.v2.services(self.service_sid).verifications.create(to=phone_number, channel="sms")
        except TwilioRestException as e:
            raise PhoneSendingFailedError(f"휴대폰 인증번호 발송 실패 {e}")

    # 인증번호 검증
    def check_verification_code(self, phone_number: str, code: str) -> None:
        try:
            verification_check = self.client.verify.v2.services(self.service_sid).verification_checks.create(
                to=phone_number, code=code
            )
        except TwilioRestException as e:
            raise PhoneVerificationCodeFailedError(f"휴대폰 인증에 실패했습니다 {e}")
        if verification_check.status != "approved":
            raise PhoneVerificationCodeFailedError("휴대폰 인증번호가 일치하지 않습니다")
