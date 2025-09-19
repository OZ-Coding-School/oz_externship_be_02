import random
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from rest_framework.exceptions import APIException, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import SocialUser, User


class KakaoService:  # 카카오 로그인 로직 담당 클래스
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"  # 카카오 토큰 발급 API URL
    USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"  # 카카오 사용자 정보 API URL

    def __init__(self) -> None:
        self.client_id = settings.KAKAO_CLIENT_ID  # 카카오 개발자 페이지 REST API
        self.redirect_uri = settings.KAKAO_REDIRECT_URI  # 카카오 개발자 페이지 redirect uri에 등록

    def get_access_token(self, code: str) -> dict[str, Any]:  # 인가 코드로 access_token 요청
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        try:
            res = requests.post(self.TOKEN_URL, data=data, timeout=5)
            res.raise_for_status()
            body: dict[str, Any] = res.json()
            access_token = body.get("access_token")
            refresh_token = body.get("refresh_token")
            access_token_expires_in = body.get("expires_in")
            refresh_token_expires_in = body.get("refresh_token_expires_in")
            if not access_token:
                raise APIException("카카오 access_token 발급 실패")
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "access_token_expires_in": access_token_expires_in,
                "refresh_token_expires_in": refresh_token_expires_in,
            }
        except requests.exceptions.RequestException as e:
            raise APIException(f"Kakao API 호출 실패: {str(e)}")

    def get_user_info(self, access_token: str) -> dict[str, Any]:  # access_token으로 사용자 정보 조회
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            res = requests.get(self.USER_INFO_URL, headers=headers, timeout=5)
            res.raise_for_status()
            body: dict[str, Any] = res.json()
            if not body.get("id"):
                raise APIException("카카오 사용자 정보 조회 실패")
            return body
        except requests.exceptions.RequestException as e:
            raise APIException(f"Kakao API 호출 실패: {str(e)}")

    def unique_nickname(self, base_nickname: str) -> str:
        # 닉네임 중복 방지
        while True:
            number = str(random.randint(1, 9999)).zfill(4)  # 항상 4자리, 최솟값 0001
            nickname = f"{base_nickname}#{number}"
            if not User.objects.filter(nickname=nickname).exists():
                return nickname

    def login_or_signup(self, kakao_user: dict[str, Any]) -> tuple[User, bool]:  # 기존 유저면 로그인, 신규면 회원가입
        kakao_id = str(kakao_user.get("id"))
        kakao_account = kakao_user.get("kakao_account", {})

        email = kakao_account.get("email")
        nickname = self.unique_nickname(kakao_account.get("profile", {}).get("nickname", "kakao_user"))
        name = kakao_account.get("name")
        phone_number = kakao_account.get("phone_number")
        birthday = kakao_account.get("birthday")
        gender = kakao_account.get("gender")
        profile_image = kakao_account.get("profile", {}).get("profile_image_url")

        try:
            social_user = SocialUser.objects.get(
                provider=SocialUser.ProviderChoices.KAKAO,
                provider_id=kakao_id,
            )
            return social_user.user, False
        except SocialUser.DoesNotExist:
            pass

            if email:
                existing_email = User.objects.filter(email=email).exists()
                if existing_email:
                    raise ValidationError("이미 가입된 이메일입니다.")

            with transaction.atomic():
                # 유저를 먼저 생성
                user = User(
                    email=email,
                    nickname=nickname,
                    phone_number=phone_number,
                    name=name,
                    birthday=birthday,
                    gender=gender,
                    profile_img_url=profile_image,
                    is_active=True,
                )
                user.set_unusable_password()
                user.save()
                # 이후에 소셜유저 생성
                SocialUser.objects.create(
                    user=user,
                    provider=SocialUser.ProviderChoices.KAKAO,
                    provider_id=kakao_id,
                )
                return user, True

    def generate_tokens(self, user: User) -> dict[str, str]:  # JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    def kakao_login(self, code: str) -> dict[str, Any]:
        # 카카오 로그인 절차
        tokens_from_kakao = self.get_access_token(code)
        kakao_access_token = tokens_from_kakao["access_token"]
        kakao_refresh_token = tokens_from_kakao.get("refresh_token")

        # 사용자 정보 조회
        kakao_user = self.get_user_info(kakao_access_token)

        # 로그인 or 회원가입
        user, created = self.login_or_signup(kakao_user)

        # JWT 토큰 발급
        jwt_tokens = self.generate_tokens(user)

        access_token_expires_in = tokens_from_kakao.get(
            "access_token_expires_in", 21599
        )  # 카카오에서 제공하는 access_token 기한 6시간
        refresh_token_expires_in = tokens_from_kakao.get(
            "refresh_token_expires_in", 5184000
        )  # 카카오에서 제공하는 refresh_token 기한 60일
        # Redis 캐시에 카카오 토큰 저장 (회원탈퇴 때 사용)
        cache.set(
            f"kakao_access_token:{user.id}",
            kakao_access_token,
            timeout=int(access_token_expires_in),
        )
        if kakao_refresh_token:
            cache.set(
                f"kakao_refresh_token:{user.id}",
                kakao_refresh_token,
                timeout=int(refresh_token_expires_in),
            )

        return {
            "message": "Kakao login successful",
            "access": jwt_tokens["access"],
            "refresh": jwt_tokens["refresh"],
            "is_new_user": created,
            "user": user,
        }