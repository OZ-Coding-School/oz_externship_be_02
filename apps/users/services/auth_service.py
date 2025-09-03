from typing import Dict, Any, TYPE_CHECKING
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.cache import cache
import os
import secrets
import base64

from apps.users.models import User

if TYPE_CHECKING:
    from typing import Final

def verify_user_email(email: str, verification_code: str) -> User:
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise serializers.ValidationError("존재하지않는 이메일입니다")

    cached_verification_code = cache.get(email)
    if cached_verification_code is None:
        raise serializers.ValidationError("인증 코드가 만료되었거나 존재하지 않습니다")
    if cached_verification_code != verification_code:
        raise serializers.ValidationError("인증코드가 일치하지않습니다")

    user.is_active = True
    user.verification_code = ""
    user.save()

    return user


def send_verification_email(email: str, verification_code: str) -> None:
    subject = "회원가입 이메일 인증"
    message = f"인증 코드를 입력하여 회원가입을 완료해주세요: {verification_code}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list)


def generate_verification_code(email: str) -> str:
    verification_code = base64.urlsafe_b64encode(secrets.token_bytes(9)).decode('utf-8')
    cache.set(email, verification_code, timeout=3600)
    return verification_code