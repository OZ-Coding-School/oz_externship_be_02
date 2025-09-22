from rest_framework import serializers

from apps.users.models import SocialUser, User


class UserResponseSerializer(serializers.ModelSerializer[User]):
    provider = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "uuid",
            "email",
            "nickname",
            "phone_number",
            "name",
            "birthday",
            "gender",
            "profile_img_url",
            "provider",
            "is_active",
            "is_staff",
            "is_superuser",
        ]

    def get_provider(self, obj: User) -> str | None:
        social_user = SocialUser.objects.filter(user=obj).first()
        return social_user.provider if social_user else None


class UserMinimalResponseSerializer(serializers.ModelSerializer[User]):
    # 로그인 응답으로 최소한의 정보만 전달
    class Meta:
        model = User
        fields = [
            "uuid",
            "email",
            "nickname",
        ]


class KakaoLoginResponseSerializer(serializers.Serializer[dict[str, object]]):
    # API 응답 스펙을 명시적으로 정의하는 클래스
    message = serializers.CharField()  # 서버가 내려주는 설명메시지 ex) 로그인 되었습니다./ 로그인 실패했습니다.
    access = serializers.CharField()  # JWT 토큰
    refresh = serializers.CharField()  # JWT 토큰
    is_new_user = serializers.BooleanField()  # 신규유저 여부
    user = UserMinimalResponseSerializer()  # Nested Serializers
