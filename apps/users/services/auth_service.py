import uuid
from smtplib import SMTPException

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response

from apps.core.utils.base62 import Base62


class EmailVerificationService:
    def verify_code(self, email: str, code: str) -> Response:
        cached_verification_code = cache.get(email)

        if cached_verification_code != code:
            return Response({"error": "인증번호가 일치하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete(email)
        return Response({"detail": "이메일 인증 성공"}, status=status.HTTP_200_OK)

    def send_verification_email(self, email: str) -> Response:
        verification_code = self.generate_verification_code()
        subject = "회원가입 이메일 인증"
        message = f"인증 코드를 입력하여 회원가입을 완료해주세요: {verification_code}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        cache.set(email, verification_code, timeout=3600)

        try:
            send_mail(subject, message, from_email, recipient_list)
            return Response({"detail": "입력하신 이메일로 인증번호가 발송되었습니다."}, status=status.HTTP_200_OK)
        except SMTPException:
            cache.delete(email)
            return Response(
                {"error": "이메일 발송 중 예외가 발생하였습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def generate_verification_code(self) -> str:
        return Base62.uuid_encode(u=uuid.uuid4())
