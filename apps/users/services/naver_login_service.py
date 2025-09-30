import json
from datetime import date, datetime
from typing import Any, Optional, cast

import requests
from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.logger import logger
from apps.users.models import SocialUser, User
from apps.users.serializers.social_login_serializers import (
    NaverUserCreateSerializer,
    NaverUserInfoSerializer,
)


class NaverService:  # 네이버 로그인 로직 담당 (카카오와 동일한 인터페이스)
    TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
    USER_INFO_URL = "https://openapi.naver.com/v1/nid/me"
    NAVER_CLIENT_ID = settings.NAVER_CLIENT_ID
    NAVER_CLIENT_SECRET = settings.NAVER_CLIENT_SECRET
    NAVER_REDIRECT_URI = settings.NAVER_REDIRECT_URI

    @classmethod
    def naver_login(cls, code: str, state: str) -> dict[str, str]:
        access_token = cls.get_access_token(code, state)
        naver_user_data = cls.get_user_info(access_token)
        user_create_data = cls._validate_naver_user_data(naver_user_data)
        return cls.process_login(user_create_data)

    @classmethod
    def process_login(cls, naver_user_data: dict[str, Any]) -> dict[str, str]:
        """
        case 1. 네이버 provider_id로 SocialUser 존재 → 해당 유저로 JWT 발급
        case 2. 같은 email의 일반 유저 존재 → SocialUser 연결 후 JWT 발급
        case 3. 신규 유저 생성 → SocialUser 연결 후 JWT 발급
        """
        provider_id = naver_user_data.pop("id")

        # 1) 기존 소셜유저
        social_user = (
            SocialUser.objects.select_related("user")
            .filter(provider=SocialUser.ProviderChoices.NAVER, provider_id=provider_id)
            .first()
        )
        if social_user is not None:
            return cls._get_tokens_for_user(social_user.user)

        # 2) 동일 이메일 유저 존재
        created_user = User.objects.filter(email=naver_user_data["email"]).first()
        if created_user is not None:
            SocialUser.objects.create(
                provider=SocialUser.ProviderChoices.NAVER, provider_id=provider_id, user=created_user
            )
            return cls._get_tokens_for_user(created_user)

        # 3) 신규 생성
        # 데이터 형식 맞춰주기
        birthday = naver_user_data.pop("birthday")
        birthyear = naver_user_data.pop("birthyear")
        naver_user_data["birthday"] = cls._parse_naver_birth_date(birthday, birthyear)
        naver_user_data["phone_number"] = naver_user_data.pop("mobile")
        naver_user_data["profile_img_url"] = naver_user_data.pop("profile_image")
        serializer = NaverUserCreateSerializer(data=naver_user_data)

        if not serializer.is_valid():
            logger.error(
                f"네이버 유저 정보를 NaverUserCreateSerializer에서 필드를 검증하는데 실패했습니다.\n\t- errors: {serializer.errors}"
            )
            raise APIException("네이버 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")

        with transaction.atomic():
            user = serializer.save()
            SocialUser.objects.create(
                user=user,
                provider=SocialUser.ProviderChoices.NAVER,
                provider_id=provider_id,
            )

        return cls._get_tokens_for_user(user)

    @classmethod
    def get_access_token(cls, code: str, state: str) -> str:
        """
        프론트에서 넘겨받은 네이버 인가 코드로 access_token 요청
        """
        response = cls._request_and_parse_response(
            url=cls.TOKEN_URL,
            method="POST",
            params={
                "grant_type": "authorization_code",
                "client_id": cls.NAVER_CLIENT_ID,
                "client_secret": cls.NAVER_CLIENT_SECRET,
                "redirect_uri": cls.NAVER_REDIRECT_URI,
                "code": code,
                "state": state,
            },
        )

        access_token = cast(str, response.get("access_token", ""))

        return access_token

    @classmethod
    def get_user_info(cls, access_token: str) -> dict[str, Any]:
        """
        access_token으로 사용자 정보 조회 → (카카오와 동일하게) serializer 검증 통과한 dict 반환
        """
        response = cls._request_and_parse_response(
            url=cls.USER_INFO_URL,
            method="GET",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return cast(dict[str, Any], response.get("response", dict()))

    @classmethod
    def _validate_naver_user_data(cls, raw: dict[str, Any]) -> dict[str, Any]:
        """
        시리얼라이저를 활용하여 네이버 유저 정보 API 응답 값 검증
        """
        serializer = NaverUserInfoSerializer(data=raw)
        if not serializer.is_valid():
            logger.error(
                f"네이버 유저 정보를 NaverUserInfoSerializer에서 필드를 검증하는데 실패했습니다.\n\t-errors: {serializer.errors}"
            )
            raise APIException("네이버 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")
        return cast(dict[str, Any], serializer.validated_data)

    @classmethod
    def _parse_naver_birth_date(cls, birthday_mmdd: str, birthyear: str) -> date:
        # 'MM-DD' + 'YYYY' -> date
        month, day = birthday_mmdd.split("-")
        return datetime.strptime(f"{birthyear}-{month}-{day}", "%Y-%m-%d").date()

    @classmethod
    def _get_tokens_for_user(cls, user: User) -> dict[str, str]:
        rt = RefreshToken.for_user(user)
        return {"access_token": str(rt.access_token), "refresh_token": str(rt)}

    @classmethod
    def _request_and_parse_response(
        cls,
        url: str,
        method: str,
        headers: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """HTTP 요청 후 status 검사 및 JSON 디코딩"""
        try:
            res = requests.request(method, url, timeout=5, headers=headers, params=params)
            if not (200 <= res.status_code < 300):
                if res.status_code == 401:
                    logger.error(
                        f"네이버 로그인 토큰 API 요청 실패.\n\t- url: {url}\n\t- status_code: {res.status_code}\n\t- response: {res.text}"
                    )
                    ext = APIException("invalid code or state.")
                    ext.status_code = status.HTTP_400_BAD_REQUEST
                    raise ext

                logger.error(
                    f"네이버 API 요청 실패\n\t- url: {url}\n\t- status_code: {res.status_code}\n\t- response: {res.text}"
                )
                raise APIException("네이버 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")
            return res.json()
        except json.JSONDecodeError as e:
            logger.error(f"네이버 로그인 API 요청 처리 도중 JSON 파싱 에러 발생.\n\t- url: {url}\n\t- error: {str(e)}")
            raise APIException("네이버 로그인에 실패했습니다. 잠시 후 다시 시도해주세요.")
