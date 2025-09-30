import json
from typing import Any, cast
from unittest.mock import MagicMock, Mock, patch

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
            "id": "naver-123",
            "email": "test@example.com",
            "name": "테스터",
            "nickname": "네닉",
            "mobile": "012-3456-7890",
            "gender": "M",
            "birthday": "12-11",
            "birthyear": "1999",
            "profile_image": "https://example.com/image.png",
        }

    def mock_naver_api(self, mock_post: Mock, mock_get: Mock) -> None:
        mock_post.return_value = self.token_response
        mock_get.return_value = self.user_response

    def test_missing_code_returns_400(self) -> None:
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.users.services.naver_login_service.requests.post")
    def test_invalid_code_or_api_failure(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = json.dumps({"error": "invalid_grant"})
        resp = self.client.post(self.url, {"code": "wrong_code", "state": "state"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.users.services.naver_login_service.NaverService.get_user_info")
    @patch("apps.users.services.naver_login_service.NaverService.get_access_token")
    def test_user_info_missing_required_attrs(self, mock_post: Mock, mock_get: Mock) -> None:
        self.mock_naver_api(mock_post, mock_get)
        mock_get.return_value = {
            "id": "naver-123",
            "name": "테스터",
            "nickname": "네닉",
            "mobile": "012-3456-7890",
            "gender": "M",
            "birthday": "12-11",
            "birthyear": "1999",
            "profile_image": "https://example.com/image.png",
        }
        resp = self.client.post(self.url, {"code": "dummy", "state": "state"})
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("네이버 로그인에 실패", resp.data["error"])

    @patch("apps.users.services.naver_login_service.NaverService.get_user_info")
    @patch("apps.users.services.naver_login_service.NaverService.get_access_token")
    def test_first_signup_with_naver_social_login(self, mock_post: MagicMock, mock_get: MagicMock) -> None:
        self.mock_naver_api(mock_post, mock_get)
        resp = self.client.post(self.url, {"code": "dummy", "state": "state"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", resp.data)
        self.assertIn("refresh_token", resp.cookies)

        social_user = SocialUser.objects.filter(
            provider=SocialUser.ProviderChoices.NAVER, provider_id=self.user_response["id"]
        ).first()
        self.assertIsNotNone(social_user)
        social_user = cast(SocialUser, social_user)
        self.assertIsNotNone(social_user.user)
        self.assertEqual(social_user.user.email, self.user_response["email"])
        self.assertEqual(social_user.user.name, self.user_response["name"])

    @patch("apps.users.services.naver_login_service.NaverService.get_user_info")
    @patch("apps.users.services.naver_login_service.NaverService.get_access_token")
    def test_email_used_user_already_exists(self, mock_post: MagicMock, mock_get: MagicMock) -> None:
        created_user = User.objects.create(
            email="test@example.com",
            name="테스터",
            nickname="네닉",
            phone_number="012-3456-7890",
            gender="M",
            birthday="1999-12-11",
            profile_img_url="https://example.com/image.png",
        )
        self.mock_naver_api(mock_post, mock_get)
        resp = self.client.post(self.url, {"code": "dummy", "state": "state"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", resp.data)
        self.assertIn("refresh_token", resp.cookies)

        social = SocialUser.objects.filter(user=created_user).first()
        self.assertIsNotNone(social)
        social = cast(SocialUser, social)
        self.assertEqual(social.user, created_user)
        self.assertEqual(social.provider_id, self.user_response["id"])
        self.assertEqual(social.provider, SocialUser.ProviderChoices.NAVER)

    @patch("apps.users.services.naver_login_service.NaverService.get_user_info")
    @patch("apps.users.services.naver_login_service.NaverService.get_access_token")
    def test_naver_social_user_already_exists(self, mock_post: MagicMock, mock_get: MagicMock) -> None:
        created_user = User.objects.create(
            email="test@example.com",
            name="테스터",
            nickname="네닉",
            phone_number="012-3456-7890",
            gender="M",
            birthday="1999-12-11",
            profile_img_url="https://example.com/image.png",
        )
        SocialUser.objects.create(
            user=created_user,
            provider_id=self.user_response["id"],
            provider=SocialUser.ProviderChoices.NAVER,
        )

        self.mock_naver_api(mock_post, mock_get)
        resp = self.client.post(self.url, {"code": "dummy", "state": "state"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", resp.data)
        self.assertIn("refresh_token", resp.cookies)
