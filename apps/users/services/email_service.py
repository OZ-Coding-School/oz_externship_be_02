import uuid
from smtplib import SMTPException
from typing import Any, Dict

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response

from apps.core.utils.base62 import Base62
from apps.users.services.exceptions import (
    EmailSendingFailedError,
    EmailVerificationCodeFailedError,
)
from apps.users.utils.enums import VerificationPurpose


class EmailVerificationService:
    def generate_verification_code(self) -> str:
        return Base62.uuid_encode(u=uuid.uuid4())

    def send_verification_email(self, email: str, purpose: VerificationPurpose, timeout: int = 300) -> None:

        verification_code = self.generate_verification_code()
        cache_key = f"{purpose.value}-{email}"
        cache.set(cache_key, verification_code, timeout=timeout)

        subject_map = {
            "signup": "회원가입 이메일 인증",
            "reset_password": "비밀번호 재설정 이메일 인증",
            "recover_account": "탈퇴 계정 복구 이메일 인증",
        }

        message_map = {
            "signup": f"인증 코드를 입력하여 회원가읍을 진행해주세요 {verification_code}",
            "reset_password": f"비밀번호 재설정을 위해 인증 코드를 입력해주세요 {verification_code}",
            "recover_account": f"탈퇴 계정 복구를 위해 인증 코드를 입력해주세요 {verification_code}",
        }

        subject = subject_map[purpose]
        message = message_map[purpose]
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list)
        except SMTPException as e:
            cache.delete(cache_key)
            raise EmailSendingFailedError(f"이메일 발송 시스템에 문제가 발생하였습니다: {e}")

    def verify_code(self, purpose: VerificationPurpose, email: str, verification_code: str) -> None:

        cache_key = f"{purpose}-{email}"
        cache_verification_code = cache.get(cache_key)

        if cache_verification_code != verification_code:
            raise EmailVerificationCodeFailedError("이메일 인증 코드가 일치하지 않습니다")

        cache.set(cache_key, verification_code, timeout=300)
