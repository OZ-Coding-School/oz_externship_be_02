# apps/users/services/user_info_service.py

from typing import Any
from rest_framework.exceptions import ValidationError
from django.core.cache import cache
from apps.users.models.user import User
from apps.users.serializers.user_info_serializer import (
    UserInfoEditSerializer,
    UserInfoSerializer,
)

#TODO 기존 번호와 동일한 번호로 변경하려고 하면 "동일한 번호입니다." 오류 생성.
#? phone_service.py에서는 인증 번호를 생성하기만 하고, 그 번호가 맞는지는 여기서 체크하니까 굳이 phone_service.py를 import할 필요는 없는 걸까?

# 휴대폰 인증 관련 캐시 키 최초 생성 함수
#? 근데 내가 캐시 키를 왜 만들려고 했더라...?
def get_phone_verification_key(phone_number: str) -> str:
    return f"phone_verification: {phone_number}"

# 인증이 완료된 휴대폰 번호를 캐시에 저장
#? 이거 필요할까? 개인적으로는 의미를 분리하는 게 명확한 상태 기록에 도움이 될 듯싶다.
def set_phone_verified(phone_number: str) -> None:
    cache.set(get_phone_verification_key(phone_number), True)

# 사용자 정보 조회
class UserInfoService:
    def __init__(self, user: User) -> None:
        self.user = user

    def get_user_info(self) -> dict:
        return UserInfoSerializer(self.user).data

# 사용자 정보 수정
class UserInfoEditService:
    def __init__(self, user: User):
        self.user = user

    def update_user_info(self, data: dict[str, Any]) -> User:
        phone_number = data.get("phone_number")

        # 기존 휴대폰 번호와 동일한 번호로 변경하려고 할 때의 예외
        if phone_number and self.user.phone_number == phone_number:
            raise ValidationError("이전과 동일한 전화번호입니다.")

        # 휴대폰 번호가 (캐시에) 있다면, 인증 검증 / 휴대폰 번호가 (캐시에) 없다면, 예외 발생
        if phone_number:
            cache_key = get_phone_verification_key(phone_number)
            if not cache.get(cache_key):
                raise ValidationError("휴대폰 인증이 필요합니다.")

        # 시리얼라이저를 통한 사용자 정보 업데이트
        serializer = UserInfoEditSerializer(instance=self.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        # 휴대폰 번호가 실제로 변경되었다면, 인증했던 캐시 삭제 후 새로운 번호로 캐시 다시 저장
        phone_number = serializer.validated_data.get("phone_number")
        if phone_number and self.user.phone_number != phone_number:
            cache.delete(get_phone_verification_key(self.user.phone_number))
            cache.set(get_phone_verification_key(phone_number), True)

        return updated_user