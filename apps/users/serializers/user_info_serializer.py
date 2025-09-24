# apps/users/serializers/user_info_serializer.py

from typing import Any, Dict

from rest_framework import serializers

from apps.users.models.user import User
from apps.users.services.phone_service import PhoneVerificationService


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

    # 인증 번호 검증
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        instance = self.instance
        new_phone = attrs.get("phone_number") # attrs: 클라이언트가 전송한 변경 데이터들
        code = attrs.get("verification_code")

        # 전화번호 변경이 없으면 인증 불필요
        if isinstance(instance, User):
            if not new_phone or instance.phone_number == new_phone:
                attrs.pop("verification_code", None) # 대비용
                return attrs

        # 휴대폰 번호를 바꿨는데 인증 코드가 없다면 에러
        if new_phone and not code:
            raise serializers.ValidationError({
                "verification_code": "휴대폰 번호 변경 시 인증 코드가 필요합니다."
            })

        # 휴대폰 번호 변경 + 코드 검증
        if new_phone and code:
            if not PhoneVerificationService.is_verified(new_phone, code):
                raise serializers.ValidationError({
                    "verification_code": "휴대폰 인증이 완료되지 않았습니다."
                })
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
    
        #? return super().create(validated_data)
    
    #? update_or_create()를 써도 괜찮으려나?
    #? https://www.django-rest-framework.org/api-guide/serializers/#saving-instances