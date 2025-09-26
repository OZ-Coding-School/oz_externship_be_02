import json
from datetime import date, datetime
from typing import Any, Optional

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.logger import logger
from apps.users.models import SocialUser, User
from apps.users.serializers.social_login_serializers import (
    KakaoUserCreateSerializer,
    KakaoUserSerializer,
)

logger = logger


class KakaoService:  # 카카오 로그인 로직 담당 클래스
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"  # 카카오 토큰 발급 API URL
    USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"  # 카카오 사용자 정보 API URL
    KAKAO_CLIENT_ID = settings.KAKAO_CLIENT_ID
    KAKAO_REDIRECT_URI = settings.KAKAO_REDIRECT_URI

    @classmethod
    def get_access_token(cls, code: str) -> Optional[str]:
        """
        프론트에서 넘겨받은 카카오 인가 코드로 access_token을 요청하는 메서드
        """
        try:
            res = requests.post(
                url=cls.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": cls.KAKAO_CLIENT_ID,
                    "redirect_uri": cls.KAKAO_REDIRECT_URI,
                    "code": code,
                },
                timeout=5,
            )

            if res.status_code == 400 and "invalid_grant" in res.text:
                raise ValidationError("invalid code")

            if not (res.status_code >= 200 and res.status_code < 300):
                raise APIException("카카오 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")

            body: dict[str, Any] = res.json()

            return body.get("access_token")
        except json.JSONDecodeError:
            raise APIException("카카오 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")

    @classmethod
    def get_user_info(cls, access_token: str) -> dict[str, str]:
        """
        access_token으로 사용자 정보 조회
        """
        try:
            res = requests.get(url=cls.USER_INFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=5)
            if not (200 <= res.status_code < 300):
                raise APIException("카카오 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")

            body: dict[str, Any] = res.json()
            return cls.validate_kakao_user_data(body)
        except json.JSONDecodeError:
            raise APIException("카카오 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")

    @classmethod
    def validate_kakao_user_data(cls, kakao_user_data: dict[str, Any]) -> dict[str, Any]:
        """
        카카오 로그인 응답 데이터가 정상적으로 들어왔는지 검증하고
        필요한 핵심 정보를 추출합니다.

        Returns:
            {
                "kakao_id": str,
                "email": str,
                "nickname": str,
                "name": str,
                "profile_image": str
            }
        Raises:
            APIException: 필수 필드가 없거나 타입이 잘못된 경우
        """
        serializer = KakaoUserSerializer(data=kakao_user_data)

        if not serializer.is_valid():
            logger.error(
                f"카카오 사용자 정보를 검증하는 데 실패했습니다. "
                f"에러: {serializer.errors}"
                f"응답 데이터: {kakao_user_data}"
            )
            raise APIException("카카오 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")

        validated_data: dict[str, Any] = serializer.validated_data.copy()

        return validated_data

    @classmethod
    def parse_kakao_birth_date(cls, birth_day: str, birth_year: str) -> date:
        day = birth_day[2:]
        month = birth_day[:2]
        birthday_string = f"{birth_year}-{month}-{day}"
        return datetime.strptime(birthday_string, "%Y-%m-%d").date()

    @classmethod
    def process_login(cls, kakao_user_data: dict[str, Any]) -> dict[str, str]:
        """
        case 1. 카카오 유저 정보에서 가져온 provider_id로 가입된 SocialUser가 있는 경우

        case 2. 카카오 유저 정보에서 가져온 email로 이메일 회원가입 유저가 존재하는 경우

        case 3. 신규 유저인 경우
        """
        # 카카오 유저 정보에서 가져온 provider_id로 연동된 소셜 계정이 있는 경우
        # SocialUser에 연동된 유저를 사용하여 RT, AT를 발급받아 리턴
        social_user = (
            SocialUser.objects.select_related("user")
            .filter(provider=SocialUser.ProviderChoices.KAKAO, provider_id=kakao_user_data["id"])
            .first()
        )
        if social_user is not None:
            rt = RefreshToken.for_user(social_user.user)
            at = str(rt.access_token)

            return {"access_token": at, "refresh_token": str(rt)}

        # 카카오 유저 정보에서 가져온 이메일로 이메일 회원가입 유저가 존재하는 경우
        # 가져온 유저를 사용하여 SocialUser를 생성하고,
        # RT, AT를 발급받아 리턴
        created_user = User.objects.filter(email=kakao_user_data["kakao_account"]["email"]).first()
        if created_user is not None:
            SocialUser.objects.create(
                provider=SocialUser.ProviderChoices.KAKAO, provider_id=kakao_user_data["id"], user=created_user
            )
            rt = RefreshToken.for_user(created_user)
            at = str(rt.access_token)

            return {"access_token": at, "refresh_token": str(rt)}

        with transaction.atomic():
            user_data = kakao_user_data["kakao_account"]
            user_data.update(user_data.pop("profile"))
            birthday = user_data.get("birthday")
            birthyear = user_data.pop("birthyear")
            user_data["birthday"] = cls.parse_kakao_birth_date(birthday, birthyear)

            serializer = KakaoUserCreateSerializer(data=user_data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            SocialUser.objects.create(
                user=user,
                provider=SocialUser.ProviderChoices.KAKAO,
                provider_id=kakao_user_data["id"],
            )

        rt = RefreshToken.for_user(user)
        at = str(rt.access_token)

        return {"access_token": at, "refresh_token": str(rt)}

    @classmethod
    def kakao_login(cls, code: str) -> dict[str, str]:
        # 카카오 로그인 절차
        kakao_access_token = cls.get_access_token(code)
        if kakao_access_token is None:
            raise APIException("카카오 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")
        # 사용자 정보 조회
        kakao_user_data = cls.get_user_info(kakao_access_token)

        # 로그인 or 회원가입
        tokens = cls.process_login(kakao_user_data)

        return tokens
