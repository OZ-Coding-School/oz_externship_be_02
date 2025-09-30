# apps/users/serializers/reset_password_serializers.py

from typing import Any, Dict

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.users.models.user import User
from apps.users.services.email_service import EmailVerificationService
from apps.users.services.exceptions import EmailVerificationCodeFailedError
from apps.users.utils.enums import VerificationPurpose

email_verify = EmailVerificationService()


class ResetPasswordSerializer(serializers.Serializer[Dict[str, Any]]):
    """
    비밀번호 재설정 요청 데이터를 검증하는 시리얼라이저
    """

    email = serializers.EmailField(required=True, help_text="이메일 주소")
    verification_code = serializers.CharField(required=True, help_text="이메일 인증 코드")
    new_password = serializers.CharField(
        required=True, write_only=True, help_text="새 비밀번호(최소 8자)"
    )  # 출력은 하지 않는다

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        email = attrs.get("email")
        verification_code = attrs.get("verification_code")
        """
        검증 로직
        """

        # 이메일 인증 코드 검증
        try:
            valid = email_verify.verify_code(
                purpose=VerificationPurpose.RESET_PASSWORD,
                email=str(email),
                verification_code=str(verification_code),
            )
        except EmailVerificationCodeFailedError:
            raise ValidationError({"verification_code": "이메일 인증 코드가 유효하지 않거나 만료되었습니다."})
        if not valid:
            raise ValidationError({"verification_code": "이메일 인증 코드가 유효하지 않습니다 "})

        return attrs

    # 검증 완료 후 저장
    def save(self, **kwargs: Any) -> User:  # type: ignore
        email = self.validated_data["email"]
        new_password = self.validated_data["new_password"]
        user = User.objects.get(email=email)
        user.set_password(new_password)  # Django 기본 검증
        user.save()
        return user
