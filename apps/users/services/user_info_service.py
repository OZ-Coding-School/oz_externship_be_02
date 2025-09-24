# apps/users/services/user_info_service.py

from typing import Any

from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import AuthenticationFailed

from apps.users.models.user import User
from apps.users.serializers.user_info_serializer import UserInfoSerializer
from apps.users.services.exceptions import PhoneVerificationCodeFailedError
from apps.users.services.phone_service import TwilioAuthService #* 수정 예정


class UserInfoService:
    def __init__(self) -> None:
        self.user: User | None = None
    #TODO 조회 로직만 추가

# 사용자 정보 수정(로그인한 사용자만 가능)
#TODO phone_service.py를 호출해서 휴대폰 인증이 된 유저만 사용할 수 있도록
class UserInfoEditService:
    def __init__(self, user: User):
        self.user = user

    def update_user_info(self, data: dict[str, Any]) -> User:
        # 이하 data에서 추출하는 용도
        phone_number = data.get("phone_number")

        # 기존 휴대폰 번호와 동일한 번호로 변경하려고 할 때의 예외
        if phone_number and self.user.phone_number == phone_number:
            raise ValidationError("이전과 동일한 전화번호입니다.")

        # 시리얼라이저를 통한 사용자 정보 업데이트
        serializer = UserInfoSerializer(instance=self.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        return updated_user