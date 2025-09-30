import json
from datetime import date, datetime
from typing import Any, cast

import requests
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import APIException, ParseError, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.logger import logger
from apps.users.models import SocialUser, User
from apps.users.serializers.social_login_serializers import (
    NaverUserCreateSerializer,
    NaverUserSerializer,
)

logger = logger


class NaverService:  # 네이버 로그인 로직 담당 (카카오와 동일한 인터페이스)
    TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
    USER_INFO_URL = "https://openapi.naver.com/v1/nid/me"
    NAVER_CLIENT_ID = settings.NAVER_CLIENT_ID
    NAVER_CLIENT_SECRET = settings.NAVER_CLIENT_SECRET
    NAVER_REDIRECT_URI = settings.NAVER_REDIRECT_URI

    @classmethod
    def get_access_token(cls, code: str) -> str:
        """
        프론트에서 넘겨받은 네이버 인가 코드로 access_token 요청
        """
        res = requests.post(
            url=cls.TOKEN_URL,
            params={
                "grant_type": "authorization_code",
                "client_id": cls.NAVER_CLIENT_ID,
                "client_secret": cls.NAVER_CLIENT_SECRET,
                "redirect_uri": cls.NAVER_REDIRECT_URI,
                "code": code,
            },
            timeout=5,
        )

        if res.status_code == 400 and "invalid" in res.text.lower():
            raise ValidationError("네이버 인가 코드가 유효하지 않습니다.")

        if not (200 <= res.status_code < 300):
            ex = APIException("네이버 토큰 발급 요청이 실패했습니다.")
            ex.status_code = 502
            raise ex
        try:
            body: dict[str, Any] = res.json()
        except ValueError:
            raise ParseError("네이버 토큰 응답 파싱에 실패했습니다.")
        token_raw: Any = body.get("access_token")
        if not isinstance(token_raw, str) or not token_raw:
            ex = APIException("네이버 토큰 응답에 access_token이 없습니다.")
            ex.status_code = 502
            raise ex
        token: str = token_raw
        return token

    @classmethod
    def _map_naver_payload_for_serializer(cls, raw: dict[str, Any]) -> dict[str, Any]:
        """
        네이버 원본 응답({resultcode, message, response:{...}}) -> NaverUserSerializer 입력 형태로 매핑
        (카카오와 동일한 serializer 구조를 맞추기 위함)
        """
        resp = raw.get("response") or {}
        return {
            "id": resp.get("id", ""),
            "naver_account": {
                "email": resp.get("email"),
                "name": resp.get("name", "이름없음"),
                "birthday": resp.get("birthday", "01-01"),  # MM-DD
                "birthyear": resp.get("birthyear", str(datetime.now().year)),
                "gender": resp.get("gender", "알수없음"),
                "profile": {
                    "nickname": resp.get("nickname", "네이버유저"),
                    "profile_image_url": resp.get("profile_image"),
                },
            },
        }

    @classmethod
    def get_user_info(cls, access_token: str) -> dict[str, Any]:
        """
        access_token으로 사용자 정보 조회 → (카카오와 동일하게) serializer 검증 통과한 dict 반환
        """
        res = requests.get(
            url=cls.USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5,
        )
        if not (200 <= res.status_code < 300):
            ex = APIException("네이버 사용자 정보 조회에 실패했습니다.")
            ex.status_code = 502
            raise ex

        try:
            raw: dict[str, Any] = res.json()
        except ValueError:
            raise ParseError("네이버 사용자 정보 응답 파싱에 실패했습니다.")

        mapped = cls._map_naver_payload_for_serializer(raw)

        serializer = NaverUserSerializer(data=mapped)
        if not serializer.is_valid():
            ex = APIException("네이버 사용자 정보 스키마가 올바르지 않습니다.")
            ex.status_code = 500
            logger.warning("NAVER_SCHEMA_INVALID errors=%s payload=%s", serializer.errors, raw)
            raise ex

        return cast(dict[str, Any], serializer.validated_data)

    @classmethod
    def parse_naver_birth_date(cls, birthday_mmdd: str, birthyear: str) -> date:
        # 'MM-DD' + 'YYYY' -> date
        month, day = birthday_mmdd.split("-")
        return datetime.strptime(f"{birthyear}-{month}-{day}", "%Y-%m-%d").date()

    @classmethod
    def process_login(cls, naver_user_data: dict[str, Any]) -> dict[str, str]:
        """
        case 1. 네이버 provider_id로 SocialUser 존재 → 해당 유저로 JWT 발급
        case 2. 같은 email의 일반 유저 존재 → SocialUser 연결 후 JWT 발급
        case 3. 신규 유저 생성 → SocialUser 연결 후 JWT 발급
        """
        provider_id = naver_user_data["id"]  # string
        account = naver_user_data["naver_account"]

        # 1) 기존 소셜유저
        social_user = (
            SocialUser.objects.select_related("user")
            .filter(provider=SocialUser.ProviderChoices.NAVER, provider_id=provider_id)
            .first()
        )
        if social_user is not None:
            rt = RefreshToken.for_user(social_user.user)
            return {"access_token": str(rt.access_token), "refresh_token": str(rt)}

        # 2) 동일 이메일 유저 존재
        email = account.get("email")
        if email:
            existed = User.objects.filter(email=email).first()
            if existed is not None:
                SocialUser.objects.create(
                    provider=SocialUser.ProviderChoices.NAVER,
                    provider_id=provider_id,
                    user=existed,
                )
                rt = RefreshToken.for_user(existed)
                return {"access_token": str(rt.access_token), "refresh_token": str(rt)}

        # 3) 신규 생성
        with transaction.atomic():
            # 카카오와 동일한 방식: account + account['profile'] 플랫화
            user_data = account.copy()
            profile = user_data.pop("profile", {})
            user_data.update(profile)

            # birthday 변환
            birthday_mmdd = user_data.get("birthday", "01-01")
            birthyear = user_data.pop("birthyear", str(datetime.now().year))
            try:
                user_data["birthday"] = cls.parse_naver_birth_date(birthday_mmdd, birthyear)
            except Exception:
                user_data["birthday"] = cls.parse_naver_birth_date("01-01", birthyear)

            # 키 매칭: profile_image_url -> User.profile_img_url
            # (이미 serializer 필드명이 profile_img_url이므로 그대로 사용)
            serializer = NaverUserCreateSerializer(data=user_data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            SocialUser.objects.create(
                user=user,
                provider=SocialUser.ProviderChoices.NAVER,
                provider_id=provider_id,
            )

        rt = RefreshToken.for_user(user)
        return {"access_token": str(rt.access_token), "refresh_token": str(rt)}

    @classmethod
    def naver_login(cls, code: str) -> dict[str, str]:
        access_token = cls.get_access_token(code)
        if access_token is None:
            raise APIException("네이버 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")
        naver_user = cls.get_user_info(access_token)
        return cls.process_login(naver_user)
