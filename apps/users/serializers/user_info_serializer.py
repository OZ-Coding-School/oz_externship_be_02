# apps/users/serializers/user_info_serializer.py

from rest_framework import serializers

from apps.users.models.user import User


# 유저 정보 조회용
class UserInfoSerializer(serializers.ModelSerializer[User]):
    profile_img_url: serializers.URLField
    email: serializers.EmailField
    nickname: serializers.CharField
    name: serializers.CharField
    phone_number: serializers.CharField
    birthday: serializers.DateField

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
class UserInfoEditSerializer(serializers.ModelSerializer[User]):
    profile_img: serializers.URLField
    password: serializers.CharField
    nickname: serializers.CharField
    phone_number: serializers.CharField

    class Meta:
        model = User
        fields = [
            "profile_img_url",
            "password",
            "nickname",
            "phone_number",
        ]
