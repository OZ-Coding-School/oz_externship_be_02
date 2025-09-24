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
    @staticmethod
    def generate_verification_code() -> str:
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
            "signup": f"인증 코드를 입력하여 회원가입을 진행해주세요 {verification_code}",
            "reset_password": f"비밀번호 재설정을 위해 인증 코드를 입력해주세요 {verification_code}",
            "recover_account": f"탈퇴 계정 복구를 위해 인증 코드를 입력해주세요 {verification_code}",
        }

        subject = subject_map[str(purpose.value)]
        message = message_map[str(purpose.value)]
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list)
        except SMTPException as e:
            cache.delete(cache_key)
            raise EmailSendingFailedError(f"이메일 발송에 실패했습니다: {e}")

    @staticmethod
    def verify_code(purpose: VerificationPurpose, email: str, verification_code: str) -> None:

        cache_key = f"{purpose}-{email}"
        cache_verification_code = cache.get(cache_key)

        if cache_verification_code != verification_code:
            raise EmailVerificationCodeFailedError("이메일 인증 코드가 일치하지 않습니다")

        cache.delete(cache_key)
        # 검증이 완료됐다는 cache.set(f"is_verified_email_{email}") -> 여기서 캐시 검증됬다는 값 비교하는 로직 추가

        # 인증 완료 상태 저장
        verified_key = f"is_verified_email_{email}_{verification_code}"
        cache.set(verified_key, True, timeout=600)

    @staticmethod
    def is_verified(email: str, verification_code: str) -> bool:
        """
        이메일 검증된 상태인지 확인
        """
        verified_key = f"is_verified_email_{email}_{verification_code}"
        return cache.get(verified_key) is True
