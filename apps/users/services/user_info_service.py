# apps/users/services/user_info_service.py

from typing import Any

from rest_framework.exceptions import ValidationError

from apps.users.models.user import User
from apps.users.serializers.user_info_serializer import UserInfoSerializer
from apps.users.services.phone_service import PhoneVerificationService


# 사용자 정보 조회: 시리얼라이저로 직렬화
class UserInfoService:
    def __init__(self, user: User) -> None:
        self.user = user

    def get_user_info(self) -> dict[str, Any]:
        return UserInfoSerializer(self.user).data


# 사용자 정보 수정(로그인한 사용자만 가능)
class UserInfoEditService:
    def __init__(self, user: User):
        self.user = user

    def update_user_info(self, data: dict[str, Any]) -> User:
        # 수정 가능한 필드를 한 줄로 추출
        profile_img_url, nickname, password, phone_number, verification_code = (
            data.get("profile_img_url"),
            data.get("nickname"),
            data.get("password"),
            data.get("phone_number"),
            data.get("verification_code"),
        )

        # 다른 회원이 이미 사용 중인 닉네임과 중복되는지 체크(자기 자신의 닉네임은 제외)
        if nickname and User.objects.exclude(pk=self.user.pk).filter(nickname=nickname).exists():
            raise ValidationError("이미 사용 중인 닉네임입니다.")

        # 비밀번호 변경 시 암호화해서 저장
        if password:
            self.user.set_password(password)
            self.user.save()  # 바뀐 비밀번호 저장
            data.pop("password")  # 시리얼라이저에 넘기지 않음

        # 시리얼라이저를 통한 사용자 정보 검증 후 저장(업데이트)
        serializer = UserInfoSerializer(instance=self.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        return updated_user
