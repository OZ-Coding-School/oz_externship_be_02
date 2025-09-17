from typing import Any, Dict

from rest_framework import serializers

from apps.users.models import User
from apps.users.services.email_service import EmailVerificationService
from apps.users.services.phone_service import TwilioAuthService, PhoneVerificationService

twilio_service = TwilioAuthService()
email_service = EmailVerificationService()
phone_service = PhoneVerificationService()

class UserSignupSerializer(serializers.ModelSerializer[User]):
    email_verification_code = serializers.CharField(write_only=True)
    phone_verification_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "email_verification_code",
            "phone_verification_code"
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value: str) -> str:
        """
        이메일 중복 확인
        """
        if User.objects.exists_email(value):
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value

    def validate_nickname(self, value: str) -> str:
        """
        닉네임 중복 확인
        """
        if User.objects.exists_nickname(value):
            raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")
        return value

    def validate_phone_number(self, value: str) -> str:
        """
        휴대폰 번호 중복 확인
        """
        if User.objects.exists_phone(value):
            raise serializers.ValidationError("이미 사용 중인 휴대폰 번호입니다.")
        return value

    def validate_email_verification_code(self, value: str) -> str:
        """
        이메일 인증 코드 검증
        """
        email = self.initial_data.get('email')
        if not email:
            raise serializers.ValidationError("이메일 주소가 필요합니다.")

        if not email_service.is_verified(email, value):
            raise serializers.ValidationError("이메일 인증 코드가 올바르지 않거나 만료되었습니다.")

        return value

    def validate_phone_verification_code(self, value: str) -> str:
        """
        휴대폰 인증 코드 검증
        """
        phone_number = self.initial_data.get('phone_number')
        if not phone_number:
            raise serializers.ValidationError("휴대폰 번호가 필요합니다.")

        if not phone_service.is_verified(phone_number=phone_number, verification_code=value):
            raise serializers.ValidationError("휴대폰 인증 코드가 올바르지 않거나 만료되었습니다.")

        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        validated_data.pop("email_verification_code", None)
        validated_data.pop("phone_verification_code", None)
        return User.objects.create_user(**validated_data)
