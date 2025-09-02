import base64
import secrets
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.users.models import User


def verify_user_email(email, verification_code):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise serializers.ValidationError({"존재하지 않는 이메일 입니다"})

    if not hasattr(user, "verification_code") or user.verification_code != verification_code:
        raise serializers.ValidationError({"인증코드가 일치하지 않습니다"})

    user.is_active = True
    user.verification_code = ""
    user.save()

    return user


def send_verification_email(email, verification_code):
    subject = "회원가입 이메일 인증"
    message = f"인증 코드를 입력하여 회원가입을 완료해주세요: {verification_code}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list)

def generate_verification_code():
    return base64.b62encode(secrets.token_bytes(9)).decode("utf-8")


