# apps/users/services/user_info_service.py

from typing import Any
from rest_framework.exceptions import ValidationError
from django.core.cache import cache
from apps.users.models.user import User
from apps.users.serializers.user_info_serializer import (
    UserInfoEditSerializer,
    UserInfoSerializer,
)

#TODO phone_service.py 가져와서 써야 할 수도 있겠는데...
#TODO 인증 번호 발송, 인증 번호 확인 등

# 휴대폰 인증 관련 캐시 키 생성 함수(일관성 유지가 목적)
def get_phone_verification_key(phone_number: str) -> str:
    return f"phone_verification: {phone_number}"

# 사용자 정보 조회
class UserInfoService:
    def __init__(self) -> None:
        self.user = User

    def get_user_info(self) -> dict:
        return UserInfoSerializer(self.user).data

# 사용자 정보 수정
class UserInfoEditService:
    def __init__(self, user: User):
        self.user = user

    def update_user_info(self, data: dict[str, Any]) -> User:
        phone_number = data.get("phone_number")

        # 휴대폰 번호가 있다면, 인증 검증
        if phone_number:
            cache_key = get_phone_verification_key(phone_number)
            if not cache.get(cache_key):
                raise ValidationError("휴대폰 인증이 필요합니다.")

        # 사용자 정보 업데이트(serializer가 처리)
        serializer = UserInfoEditSerializer(instance=self.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        # 휴대폰 번호가 실제로 변경되었다면, 인증했던 캐시 삭제
        if phone_number and self.user.phone_number != phone_number:
            cache.delete(get_phone_verification_key(phone_number))

        return updated_user