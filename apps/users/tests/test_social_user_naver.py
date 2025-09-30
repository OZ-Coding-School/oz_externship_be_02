import json
from typing import Any
from unittest.mock import Mock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import SocialUser, User
from apps.users.services.naver_login_service import NaverService


class TestNaverLogin(APITestCase):
    url: str
    token_response: dict[str, Any]
    user_response: dict[str, Any]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("naver_callback")
        cls.token_response = {"access_token": "fake_access_token", "refresh_token": "fake_refresh_token"}
        cls.user_response = {
            "resultcode": "00",
            "message": "success",
            "response": {
                "id": "naver-123",
                "email": "test@example.com",
                "name": "테스터",
                "nickname": "네닉",
                "gender": "M",
                "birthday": "12-11",
                "birthyear": "1999",
                "profile_image": "https://example.com/image.png",
            },
        }

    def mock_naver_api(self, mock_post: Mock, mock_get: Mock) -> None:
        mock_post.return_value.json.return_value = self.token_response
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = ""
        mock_get.return_value.json.return_value = self.user_response
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = ""

    def test_missing_code_returns_400(self) -> None:
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.users.services.naver_login_service.requests.post")
    def test_invalid_code_or_api_failure(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = json.dumps({"error": "invalid_grant"})
        resp = self.client.post(self.url, {"code": "wrong_code"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.users.services.naver_login_service.requests.get")
    @patch("apps.users.services.naver_login_service.requests.post")
    def test_user_info_missing_required_attrs(self, mock_post: Mock, mock_get: Mock) -> None:
        self.mock_naver_api(mock_post, mock_get)
        mock_get.return_value.json.return_value = {
            "resultcode": "00",
            "message": "success",
            "response": {
                # 'id' 누락 같은 케이스
                "email": "test@example.com",
            },
        }
        resp = self.client.post(self.url, {"code": "dummy"})
        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(resp.data.get("error"), "네이버 사용자 정보 스키마가 올바르지 않습니다.")

    @patch("apps.users.services.naver_login_service.requests.get")
    @patch("apps.users.services.naver_login_service.requests.post")
    def test_email_already_used(self, mock_post: Mock, mock_get: Mock) -> None:
        User.objects.create(
            email="test@example.com",
            nickname="normaluser",
            is_active=True,
            birthday="2000-02-02",
            name="normaluser",
            phone_number="010-2234-5678",
            gender="male",
        )
        self.mock_naver_api(mock_post, mock_get)
        resp = self.client.post(self.url, {"code": "d"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", resp.data)
        self.assertNotIn("refresh_token", resp.data)

        self.assertIn("refresh_token", resp.cookies)
        rt_cookie = resp.cookies["refresh_token"]

        self.assertTrue(rt_cookie["httponly"])
        self.assertEqual(rt_cookie["samesite"], "None")
        self.assertEqual(rt_cookie["domain"], ".ozcoding.site")
        self.assertTrue(rt_cookie["secure"])


class TestNaverLoginServiceCoverage(APITestCase):
    url: str
    token_ok: dict[str, Any]
    user_ok: dict[str, Any]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("naver_callback")
        cls.token_ok = {"access_token": "at", "refresh_token": "rt"}
        cls.user_ok = {
            "resultcode": "00",
            "message": "success",
            "response": {
                "id": "naver-123",
                "email": "new_user@example.com",
                "name": "네이버유저",
                "nickname": "네닉",
                "gender": "F",
                "birthday": "03-14",
                "birthyear": "1995",
                "profile_image": "https://example.com/p.png",
            },
        }

    def _mock_naver(
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

    @patch("apps.users.services.naver_login_service.requests.get")
    @patch("apps.users.services.naver_login_service.requests.post")
    def test_token_api_non_2xx(self, mock_post: Mock, mock_get: Mock) -> None:
        self._mock_naver(mock_post, mock_get, post_status=502)
        mock_post.return_value.text = "Bad Gateway"
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(resp.data.get("error"), "네이버 토큰 발급 요청이 실패했습니다.")

    @patch("apps.users.services.naver_login_service.requests.get")
    @patch("apps.users.services.naver_login_service.requests.post")
    def test_token_api_malformed_json(self, mock_post: Mock, mock_get: Mock) -> None:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.side_effect = json.JSONDecodeError("x", "x", 0)
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("error"), "네이버 토큰 응답 파싱에 실패했습니다.")

    @patch("apps.users.services.naver_login_service.requests.get")
    @patch("apps.users.services.naver_login_service.requests.post")
    def test_user_info_api_non_2xx(self, mock_post: Mock, mock_get: Mock) -> None:
        self._mock_naver(mock_post, mock_get, get_status=500)
        mock_get.return_value.text = "Internal Server Error"
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(resp.data.get("error"), "네이버 사용자 정보 조회에 실패했습니다.")

    @patch("apps.users.services.naver_login_service.requests.get")
    @patch("apps.users.services.naver_login_service.requests.post")
    def test_user_info_malformed_json(self, mock_post: Mock, mock_get: Mock) -> None:
        self._mock_naver(mock_post, mock_get)
        mock_get.return_value.json.side_effect = json.JSONDecodeError("x", "x", 0)
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("error"), "네이버 사용자 정보 응답 파싱에 실패했습니다.")

    @patch("apps.users.services.naver_login_service.logger")
    @patch("apps.users.services.naver_login_service.requests.get")
    @patch("apps.users.services.naver_login_service.requests.post")
    def test_validate_naver_user_data_logs_and_raises(self, mock_post: Mock, mock_get: Mock, mock_logger: Mock) -> None:
        bad_body: dict[str, Any] = {"resultcode": "00", "message": "success", "response": {}}  # id 누락
        self._mock_naver(mock_post, mock_get, get_json=bad_body)
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertTrue(mock_logger.warning.called)
        self.assertEqual(resp.data.get("error"), "네이버 사용자 정보 스키마가 올바르지 않습니다.")

    @patch("apps.users.services.naver_login_service.requests.get")
    @patch("apps.users.services.naver_login_service.requests.post")
    def test_access_token_missing_leads_to_502(self, mock_post: Mock, mock_get: Mock) -> None:
        self._mock_naver(mock_post, mock_get, post_json={"refresh_token": "rt"})
        resp = self.client.post(self.url, {"code": "c"})
        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(resp.data.get("error"), "네이버 토큰 응답에 access_token이 없습니다.")

    @patch("apps.users.services.naver_login_service.requests.get")
    @patch("apps.users.services.naver_login_service.requests.post")
    def test_success_new_user_created(self, mock_post: Mock, mock_get: Mock) -> None:
        self._mock_naver(mock_post, mock_get)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(SocialUser.objects.count(), 0)

        resp = self.client.post(self.url, {"code": "ok"})
        self.assertNotIn("refresh_token", resp.data)
        self.assertIn("refresh_token", resp.cookies)
        rt_cookie = resp.cookies["refresh_token"]
        self.assertTrue(rt_cookie["httponly"])
        self.assertEqual(rt_cookie["samesite"], "None")
        self.assertEqual(rt_cookie["domain"], ".ozcoding.site")
        self.assertTrue(rt_cookie["secure"])

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
            provider=SocialUser.ProviderChoices.NAVER,
            provider_id="naver-123",
        )

        # 서비스가 기대하는 형태(NaverUserSerializer validated_data)
        naver_payload: dict[str, Any] = {
            "id": "naver-123",
            "naver_account": {"email": "relogin@example.com", "profile": {"nickname": "old"}},
        }

        tokens = NaverService.process_login(naver_payload)

        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(SocialUser.objects.count(), 1)
