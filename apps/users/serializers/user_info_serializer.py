# apps/users/serializers/user_info_serializer.py

from typing import Any, Dict

from rest_framework import serializers

from apps.users.models.user import User
from apps.users.services.phone_service import PhoneVerificationService


# 유저 정보 직렬화
class UserInfoSerializer(serializers.ModelSerializer[User]):
    # write_only = True: 응답에는 포함되지 않음
    verification_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "profile_img_url",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "verification_code",
        ]

    # 인증 코드 검증
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        instance = getattr(self, "instance", None)  # self에 instance 속성이 없다면 None을 반환
        new_phone = attrs.get("phone_number")  # attrs: 클라이언트가 전송한 변경 데이터들
        code = attrs.get("verification_code")

        # 휴대폰 번호를 변경하지 않았다면 인증 코드 검증 불필요
        # * 1) instance가 있고,
        # * 2) new_phone이 없거나 new_phone이 기존 instance의 phone_number와 같다면,
        # * 3) 인증 코드를 제거한 뒤 검증하지 않음
        # * if instance and new_phone == instance.phone_number는 new_phone이 기존 instance의 phone_number와 같을 때만 실행됨
        if instance and (not new_phone or instance.phone_number == new_phone):
            attrs.pop("verification_code", None)  # 인증 코드 제거
            return attrs

        # 휴대폰 번호를 바꿨는데 인증 코드가 없다면 에러
        if new_phone and not code:
            raise serializers.ValidationError({"verification_code": "휴대폰 번호 변경 시 인증 코드가 필요합니다."})

        # 휴대폰 번호 변경 + 코드 검증
        if new_phone and code:
            if not PhoneVerificationService.is_verified(new_phone, code):
                raise serializers.ValidationError({"verification_code": "휴대폰 인증이 완료되지 않았습니다."})

        # 검증 완료 시 verification_code 제거
        attrs.pop("verification_code", None)
        return attrs

    # 검증 후 실제 반영: setattr이 모든 필드를 덮어쓰기 때문에 허용 필드 관리 필수
    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        validated_data.pop("verification_code", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)  # User 모델의 속성에 반영

        instance.save()
        return instance
