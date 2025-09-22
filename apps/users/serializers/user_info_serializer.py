# apps/users/serializers/user_info_serializer.py

from rest_framework import serializers

from apps.users.models.user import User


# 유저 정보 조회용
class UserInfoSerializer(serializers.ModelSerializer[User]):
    profile_img_url = serializers.URLField()
    email = serializers.EmailField()
    nickname = serializers.CharField()
    name = serializers.CharField()
    phone_number = serializers.CharField()
    birthday = serializers.DateField()

    class Meta:
        model = User
        fields = [
            "profile_img_url",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
        ]


# 유저 정보 수정용
# write_only: 서버에 전달만 하고 응답에는 포함하지 않음
class UserInfoEditSerializer(serializers.ModelSerializer[User]):
    profile_img_url = serializers.URLField(required=False)
    password = serializers.CharField(required=False, write_only=True)
    nickname = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    is_phone_number_verified = serializers.BooleanField(required=False, write_only=True)
    # True: 인증 완료 / False: 인증 미완료(인증 필요)

    class Meta:
        model = User
        fields = [
            "profile_img_url",
            "password",
            "nickname",
            "phone_number",
            "is_phone_number_verified",
        ]

    # 비밀번호 암호화
    def update(self, instance: User, validated_data: dict) -> User:
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)