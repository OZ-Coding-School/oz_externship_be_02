from datetime import date, timedelta
from http.cookies import Morsel
from typing import cast

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.tests.mixins.test_user_mixins import VerificationMixin
from apps.users.models import Withdrawals, User


class AuthTokenViewsTests(APITestCase, VerificationMixin):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.email = "test@example.com"
        cls.password = "testpassword"
        cls.user = cls._create_test_user(email=cls.email, password=cls.password, is_active=True)
        cls.refresh_url = reverse("token_refresh")
        cls.revoke_url = reverse("logout")
        cls.login_url = reverse("email_login")

    def test_email_login_success_and_set_refresh_cookie(self) -> None:
        """
        로그인시 액세스 토큰은 응답바디 리프레시토큰은 쿠키인지 확인
        """
        response = self.client.post(self.login_url, {"email": self.email, "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.cookies)

    def test_login_failed(self) -> None:
        """
        로그인 실패 케이스
        """
        response = self.client.post(self.login_url, {"email": self.email, "password": "wrossngpassword1"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_refresh_access_token(self) -> None:
        """
        쿠키 기반 refresh로 access 토큰 재발급
        """
        # 1.로그인 해서 액세스,리프레시 토큰 발급(refresh만 쿠키로)
        login_response = self.client.post(self.login_url, {"email": self.email, "password": self.password})
        # 2. 발급받은 토큰으로 요청
        refresh_cookie = cast(Morsel[str], login_response.cookies.get("refresh_token"))
        self.assertIsNotNone(refresh_cookie)
        # 3. 쿠키로 받은 리프레시 쿠키도 같이 요청
        self.client.cookies["refresh_token"] = refresh_cookie.value
        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_issue_failed(self) -> None:
        """
        토큰 재발급 실패 케이스
        """

        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_logout_success_and_delete_cookie(self) -> None:
        """
        로그아웃 성공 케이스
        """
        # 1. 로그인 -> refresh 토큰 발급
        response = self.client.post(self.login_url, {"email": self.email, "password": self.password})

        refresh_cookie = cast(Morsel[str], response.cookies.get("refresh_token"))

        # 2. refresh 쿠키 포함해서 로그아웃 요청
        self.client.cookies["refresh_token"] = refresh_cookie.value
        response = self.client.post(self.revoke_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "로그아웃이 완료되었습니다")
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_logout_without_refresh_cookie(self) -> None:
        """
        쿠키에 refresh 토큰이 없는 경우
        """
        response = self.client.post(self.revoke_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "refresh 토큰이 필요합니다")

    def test_logout_with_invalid_refresh_token(self) -> None:
        """
        블랙리스트 처리 또는 유효하지않은 refresh 인 경우
        """
        # 잘못된 토큰을 쿠키에 넣음
        self.client.cookies["refresh_token"] = "invalidtoken123"
        response = self.client.post(self.revoke_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("리프레시 토큰이 유효하지 않습니다", response.data["error"])

class InactiveUserLoginTestCase(APITestCase, VerificationMixin):

    @classmethod
    def setUpTestData(cls) -> None:

        # 1) 탈퇴 계정 생성
        cls.user = User.objects.create_user(
            email="inactive@example.com",
            password="testpassword",
            is_active=False,  # 탈퇴 상태

            name= "테스트유저",
            nickname= "tester",
            phone_number= "01012345678",
            gender= "M",
            birthday= "2000-01-01",
            )

        # 2) 탈퇴 요청 생성 + due_date 지정
        cls.withdrawal = Withdrawals.objects.create(
            user=cls.user,
            due_date=date.today() + timedelta(days=14)
        )

        cls.login_url = reverse("email_login")

    def test_inactive_user_login_due_date(self) -> None:
        """
        탈퇴 계정 로그인 시 due_date가 반환되는지 확인
        """
        response = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": "testpassword"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

        # error가 dict 형태인지 확인 후 due_date 검증
        error_detail = response.data["error"]
        self.assertIsInstance(error_detail, dict)
        self.assertIn("due_date", error_detail)
        self.assertEqual(
            error_detail["due_date"],
            self.withdrawal.due_date.isoformat()
        )

        self.assertIn("detail", error_detail)
        self.assertEqual(
            error_detail["detail"],
            "탈퇴 계정입니다. 복구 가능 기간 확인 바랍니다."
        )