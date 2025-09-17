from typing import Any, Dict

from rest_framework import serializers

from apps.users.models import User
from apps.users.services.email_service import EmailVerificationService
from apps.users.services.exceptions import PhoneVerificationCodeFailedError
from apps.users.services.phone_service import TwilioAuthService
from apps.users.utils.enums import VerificationPurpose

twilio_service = TwilioAuthService()
email_service = EmailVerificationService()


class UserSignupSerializer(serializers.ModelSerializer[User]):

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

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        이메일, 휴대폰 인증코드 검증 + 최종 인증 여부
        """
        email = attrs["email"]
        phone_number = attrs["phone_number"]

        # 인증 코드 가져오기
        phone_code = self.initial_data.get("phone_verification_code")
        email_code = self.initial_data.get("email_verification_code")

        # 휴대폰 검증 코드
        if not phone_code:
            raise serializers.ValidationError({"phone_number": "휴대폰 인증 코드가 필요합니다"})

        try:
            twilio_service.check_verification_code(phone_number=phone_number, code=phone_code)
        except PhoneVerificationCodeFailedError as e:
            raise serializers.ValidationError({"phone_number": str(e)})

        # 이메일 검증 코드
        if not email_code:
            raise serializers.ValidationError("이메일 인증 코드가 필요합니다")
        email_service.verify_code(purpose=VerificationPurpose.SIGNUP, email=email, verification_code=email_code)

        # 인증 여부 확인
        if not email_service.is_verified(email, email_code):
            raise serializers.ValidationError({"email": " 이메일 인증이 완료되지 않았습니다"})

        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
