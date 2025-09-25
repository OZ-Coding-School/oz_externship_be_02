# apps/users/serializers/user_info_serializer.py

from typing import Any, Dict

from rest_framework import serializers

from apps.users.models.user import User


# 유저 정보 직렬화
class UserInfoSerializer(serializers.ModelSerializer[User]):
    # write_only = True: 응답에는 포함되지 않음
    # required = False: 휴대폰 번호를 바꾸는 게 아니라면 필수로 요구하지는 않음
    verification_code = serializers.CharField(write_only=True, required=False)

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

    # 인증 코드 검증은 서비스에서 수행하므로 여기서는 제거만 처리
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # 검증 완료 시 verification_code 제거
        attrs.pop("verification_code", None)
        return attrs

    # 검증 후 실제 반영: setattr이 모든 필드를 덮어쓰기 때문에 허용 필드 관리 필수
    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        validated_data.pop("verification_code", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value) # User 모델의 속성에 반영

        instance.save()
        return instance
