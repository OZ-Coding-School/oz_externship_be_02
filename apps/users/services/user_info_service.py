# apps/users/services/user_info_service.py

from typing import Any

from django.core.cache import cache
from rest_framework.exceptions import ValidationError

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

# 휴대폰 인증 서비스
class PhoneVerificationService:
    def __init__(self, phone_number: str, is_verified: bool):
        self.phone_number = phone_number
        self.is_verified = is_verified

    def validate(self) -> None:
        """
        휴대폰 번호를 수정하려고 하면 인증이 완료되었는지를 확인함.
        인증되지 않았다면 ValidationError 발생.
        """
        # is_verified가 False라면
        if not self.is_verified:
            raise ValidationError("휴대폰 인증이 필요합니다.")
        
        # 캐시에 인증된 번호가 없다면
        cache_key = get_phone_verification_key(self.phone_number)
        if not cache.get(cache_key):
            raise ValidationError("인증된 휴대폰 번호가 아닙니다.")
        
    def clear_cache(self) -> None:
        """
        인증된 휴대폰 번호가 바뀌었다면, 휴대폰 번호를 업데이트하고 이전 번호를 삭제.
        """
        cache_key = get_phone_verification_key(self.phone_number)
        cache.delete(cache_key)

class UserInfoEditService:
    def __init__(self, user: User):
        self.user = user

    def update_user_info(self, data: dict[str, Any]) -> User:
        phone_number = data.get("phone_number")
        is_verified = data.get("is_phone_number_verified", False)

        # 휴대폰 번호가 있다면, 인증 검증
        if phone_number:
            PhoneVerificationService(phone_number, is_verified).validate()

        # 사용자 정보 업데이트(serializer 처리)
        serializer = UserInfoEditSerializer(instance=self.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        # 휴대폰 번호가 실제로 변경되었다면, 인증했던 캐시 삭제
        if phone_number and self.user.phone_number != phone_number:
            PhoneVerificationService(phone_number, is_verified).clear_cache()

        return updated_user