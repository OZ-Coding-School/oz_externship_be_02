import json
from typing import Any
from unittest.mock import MagicMock, Mock, patch

from django.urls import reverse
from requests import Response
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.services.kakao_login_service import KakaoService
from apps.users.models import SocialUser, User


class TestKakaoLogin(APITestCase):
    url: str
    token_response: dict[str, Any]
    user_response: dict[str, Any]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("kakao_callback")

        cls.token_response = {
            "access_token": "fake_access_token",
            "refresh_token": "fake_refresh_token",
        }

        cls.user_response = {
            "id": 12345,
            "kakao_account": {
                "email": "test@example.com",
                "name": "test",
                "birthday": "1211",
                "birthyear": "1999",
                "gender": "M",
                "phone_number": "010-1234-1111",
                "profile": {
                    "nickname": "test",
                    "profile_image_url": "https://example.com/image.png",
                },
            },
        }

    def mock_kakao_api(self, mock_post: Mock, mock_get: Mock) -> None:
        mock_post.return_value.json.return_value = self.token_response
        mock_post.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.user_response
        mock_get.return_value.status_code = 200

    def test_missing_code_returns_400(self) -> None:
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.users.services.kakao_login_service.requests.post")
    def test_invalid_code_or_api_failure(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = json.dumps({"error": "invalid_grant", "error_description": "invalid code"})
        response = self.client.post(self.url, {"code": "wrong_code"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.users.services.kakao_login_service.requests.get")
    @patch("apps.users.services.kakao_login_service.requests.post")
    def test_user_info_missing_required_attrs(self, mock_post: Mock, mock_get: Mock) -> None:
        self.mock_kakao_api(mock_post, mock_get)
        mock_get.return_value.json.return_value = {
            "kakao_account": {
                "email": "test@example.com",
                "name": "test",
                "gender": "M",
                "phone_number": "010-1234-1111",
                "profile": {
                    "nickname": "test",
                    "profile_image_url": "https://example.com/image.png",
                },
            },
        }

        response = self.client.post(self.url, {"code": "dummy_code"})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("카카오 로그인에 실패", response.data["error"])

    @patch("apps.users.services.kakao_login_service.requests.post")
    @patch("apps.users.services.kakao_login_service.requests.get")
    def test_email_already_used(self, mock_get: Mock, mock_post: Mock) -> None:
        User.objects.create(
            email="test@example.com",
            nickname="normaluser",
            is_active=True,
            birthday="2000-02-02",
            name="normaluser",
            phone_number="010-2234-5678",
            gender="male",
        )

        self.mock_kakao_api(mock_post, mock_get)

        response = self.client.post(self.url, {"code": "dummy_code"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)


class TestKakaoLoginServiceCoverage(APITestCase):
    url: str
    token_ok: dict[str, Any]
    user_ok: dict[str, Any]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("kakao_callback")
        cls.token_ok = {"access_token": "at", "refresh_token": "rt"}
        # KakaoUserSerializer에서 id는 IntegerField → 정수/숫자문자열 모두 허용되지만 정수 사용 권장
        cls.user_ok = {
            "id": 12345,
            "kakao_account": {
                "email": "new_user@example.com",
                "name": "카카오유저",
                "birthday": "1211",
                "birthyear": "1999",
                "gender": "male",
                "phone_number": "010-1111-2222",
                "profile": {
                    "nickname": "카카오닉",
                    "profile_image_url": "https://example.com/p.png",
                },
            },
        }

    # 공통 mock helper
    def _mock_kakao(
        self,
        mock_post: Mock,
        mock_get: Mock,
        *,
        post_status: int = 200,
        get_status: int = 200,
        post_json: dict[str, Any] | None = None,
        get_json: dict[str, Any] | None = None,
    ) -> None:
        mock_post.return_value.status_code = post_status
        mock_post.return_value.json.return_value = self.token_ok if post_json is None else post_json
        mock_post.return_value.text = ""
        mock_get.return_value.status_code = get_status
        mock_get.return_value.json.return_value = self.user_ok if get_json is None else get_json
        mock_get.return_value.text = ""

    @patch("apps.users.services.kakao_login_service.requests.get")
    @patch("apps.users.services.kakao_login_service.requests.post")
    def test_token_api_non_2xx(self, mock_post: Mock, mock_get: Mock) -> None:
        self._mock_kakao(mock_post, mock_get, post_status=502)
        mock_post.return_value.text = "Bad Gateway"
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("카카오 로그인에 실패", resp.data["error"])

    @patch("apps.users.services.kakao_login_service.requests.get")
    @patch("apps.users.services.kakao_login_service.requests.post")
    def test_token_api_malformed_json(self, mock_post: Mock, mock_get: Mock) -> None:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.side_effect = json.JSONDecodeError("x", "x", 0)
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("카카오 로그인에 실패", resp.data["error"])

    @patch("apps.users.services.kakao_login_service.requests.get")
    @patch("apps.users.services.kakao_login_service.requests.post")
    def test_user_info_api_non_2xx(self, mock_post: Mock, mock_get: Mock) -> None:
        self._mock_kakao(mock_post, mock_get, get_status=500)
        mock_get.return_value.text = "Internal Server Error"
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("카카오 로그인에 실패", resp.data["error"])

    @patch("apps.users.services.kakao_login_service.requests.get")
    @patch("apps.users.services.kakao_login_service.requests.post")
    def test_user_info_malformed_json(self, mock_post: Mock, mock_get: Mock) -> None:
        self._mock_kakao(mock_post, mock_get)
        mock_get.return_value.json.side_effect = json.JSONDecodeError("x", "x", 0)
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("카카오 로그인에 실패", resp.data["error"])

    @patch("apps.users.services.kakao_login_service.logger")
    @patch("apps.users.services.kakao_login_service.requests.get")
    @patch("apps.users.services.kakao_login_service.requests.post")
    def test_validate_kakao_user_data_logs_and_raises(self, mock_post: Mock, mock_get: Mock, mock_logger: Mock) -> None:
        bad_body: dict[str, Any] = {"kakao_account": {}}  # 필드 다 빠져서 serializer invalid
        self._mock_kakao(mock_post, mock_get, get_json=bad_body)
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue(mock_logger.error.called)

    @patch("apps.users.services.kakao_login_service.requests.get")
    @patch("apps.users.services.kakao_login_service.requests.post")
    def test_access_token_missing_leads_to_500(self, mock_post: Mock, mock_get: Mock) -> None:
        self._mock_kakao(mock_post, mock_get, post_json={"refresh_token": "rt"})
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("카카오 로그인에 실패", resp.data["error"])

    @patch("apps.users.services.kakao_login_service.requests.get")
    @patch("apps.users.services.kakao_login_service.requests.post")
    def test_success_new_user_created(self, mock_post: Mock, mock_get: Mock) -> None:
        self._mock_kakao(mock_post, mock_get)  # 정상 토큰/유저 응답
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(SocialUser.objects.count(), 0)

        resp = self.client.post(self.url, {"code": "ok"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", resp.data)
        self.assertIn("refresh_token", resp.data)

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(SocialUser.objects.count(), 1)

    def test_process_login_existing_social_user_branch(self) -> None:
        user = User.objects.create(
            email="relogin@example.com",
            nickname="old",
            is_active=True,
            birthday="1990-01-01",
            name="old",
            phone_number="010-0000-0000",
            gender="male",
        )
        SocialUser.objects.create(
            user=user,
            provider=SocialUser.ProviderChoices.KAKAO,
            provider_id=12345,  # setUpTestData의 user_ok["id"]와 동일
        )

        kakao_payload: dict[str, Any] = {
            "id": 12345,
            "kakao_account": {"email": "relogin@example.com"},
        }

        tokens = KakaoService.process_login(kakao_payload)

        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(SocialUser.objects.count(), 1)