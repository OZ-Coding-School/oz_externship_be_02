from typing import Any

from rest_framework import serializers

from apps.users.models import User


class SocialLoginCallbackRequestSerializer(serializers.Serializer[dict[str, str]]):
    code = serializers.CharField(help_text="인가 코드")


class KakaoUserCreateSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["email", "nickname", "profile_img_url", "name", "gender", "phone_number", "birthday"]

    def create(self, validated_data: dict[str, Any]) -> User:
        user = User(**validated_data)
        user.is_active = True
        user.set_unusable_password()
        user.save()
        return user


class KakaoProfileSerializer(serializers.Serializer[dict[str, Any]]):
    nickname = serializers.CharField()
    profile_image_url = serializers.URLField(required=False, allow_null=True)


class KakaoAccountSerializer(serializers.Serializer[dict[str, Any]]):
    email = serializers.EmailField()
    name = serializers.CharField(required=False, default="이름없음")
    birthday = serializers.RegexField(regex=r"^\d{4}$")
    birthyear = serializers.RegexField(regex=r"^\d{4}$")
    profile = KakaoProfileSerializer()
    gender = serializers.CharField()


class KakaoUserSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    kakao_account = KakaoAccountSerializer()
