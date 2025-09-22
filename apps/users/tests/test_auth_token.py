from rest_framework.test import APITestCase, override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse

from apps.core.tests.mixins.test_user_mixins import VerificationMixin
from apps.users.models import User


class AuthTokenViewsTests(APITestCase, VerificationMixin):
    @classmethod
    def setUpTestData(cls):
        cls.email ="test@example.com"
        cls.password = "testpassword"
        cls.is_active = True
        cls.user = cls._create_test_user(email='test@example.com')
        cls.refresh_url = reverse("token_refresh")
        cls.revoke_url = reverse("logout")
        cls.login_url = reverse("email_login")

    def test_email_login_success_and_set_refresh_cookie(self):
        """
        로그인시 액세스 토큰은 응답바디 리프레시토큰은 쿠키인지 확인
        """
        response = self.client.post(self.login_url, {"email": (email := self.email), "password" :(password:= self.password)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.cookies)

    def test_login_failed(self):
        """
        로그인 실패 케이스
        """
        response = self.client.post(self.login_url, {"email": (email := self.email), "password" :(password:= "wrongpassowrd")})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)
    def test_refresh_access_token(self):
        """
        쿠키 기반 refresh로 access 토큰 재발급
        """
        # 1.로그인 해서 액세스,리프레시 토큰 발급(refresh만 쿠키로)
        login_response = self.client.post(self.login_url, {"email" : (email :=self.email), "password" : (password :=self.password)})
        # 2. 발급받은 토큰으로 요청
        refresh_cookie = login_response.cookies.get("refresh")
        # 3. 쿠키로 받은 리프레시 쿠키도 같이 요청
        self.client.cookies["refresh"] = refresh_cookie
        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_issue_failed(self):
        """
        토큰 재발급 실패 케이스
        """
        response = self.client.post(self.refresh_url, {"email": (email := self.email), "password" :(password:= self.password)})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_logout_success_and_delete_cookie(self):
        """
        로그아웃 성공 케이스
        """
        # 1. 로그인 -> refresh 토큰 발급
        response = self.client.post(self.login_url, {"email": (email := self.email), "password" :(password:= self.password)})

        refresh_cookie = response.cookies.get("refresh")

        # 2. refresh 쿠키 포함해서 로그아웃 요청
        self.client.cookies["refresh"] = refresh_cookie.value
        response = self.client.post(self.revoke_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "로그아웃이 완료되었습니다")
        self.assertEqual(response.cookies["refresh"].value, "")

    def test_logout_without_refresh_cookie(self):
        """
       쿠키에 refresh 토큰이 없는 경우
        """
        response = self.client.post(self.revoke_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "refresh 토큰이 필요합니다")

    def test_logout_with_invalid_refresh_token(self):
        """
        블랙리스트 처리 또는 유효하지않은 refresh 인 경우
        """
        # 잘못된 토큰을 쿠키에 넣음
        self.client.cookies['refresh'] = "invalidtoken123"
        response = self.client.post(self.revoke_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("리프레시 토큰이 유효하지 않습니다", response.data["error"])