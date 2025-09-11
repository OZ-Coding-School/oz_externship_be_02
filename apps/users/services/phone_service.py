from typing import Any, Dict

from django.conf import settings
from twilio.rest import Client  # type: ignore


class TwilioAuthService:
    def __init__(self) -> None:
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.service_sid = settings.TWILIO_VERIFY_SERVICE_SID

    # 인증번호 전송
    def send_verification_code(self, phone_number: str) -> dict[str, Any]:
        try:
            self.client.verify.v2.services(self.service_sid).verifications.create(to=phone_number, channel="sms")
            return {"success": True, "message": "인증번호 전송 되었습니다"}
        except Exception as e:
            return {"success": False, "message": "전송 실패했습니다"}

    # 인증번호 검증
    def check_verification_code(self, phone_number: str, code: str) -> dict[str, Any]:
        try:
            verification_check = self.client.verify.v2.services(self.service_sid).verification_checks.create(
                to=phone_number, code=code
            )
            if verification_check.status == "approved":
                return {"success": True, "message": "휴대폰 인증 완료"}
            return {"success": False, "message": "인증번호가 일치하지 않습니다"}
        except Exception as e:
            return {"success": False, "message": "인증 실패: 서버 오류"}
