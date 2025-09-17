from typing import Any
from unittest.mock import ANY, Mock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
            "expires_in": 21599,
            "refresh_token_expires_in": 5184000,
        }

        cls.user_response = {
            "id": "12345",
            "kakao_account": {
                "email": "test@example.com",
                "profile": {
                    "nickname": "testuser",
                    "profile_image_url": "http://example.com/image.png",
                },
                "name": "김오즈",
                "phone_number": "010-1234-5678",
                "birthday": "2000-01-01",
                "gender": "male",
            },
        }

    def test_missing_code_returns_400(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "code is required")

    @patch("apps.users.services.social_user.cache.set")
    def test_successful_login_flow(self, mock_cache_set: Mock) -> None:
        with (
            patch("apps.users.services.social_user.requests.post") as mock_post,
            patch("apps.users.services.social_user.requests.get") as mock_get,
        ):
            mock_post.return_value.json.return_value = self.token_response
            mock_post.return_value.raise_for_status = lambda: None
            mock_get.return_value.json.return_value = self.user_response
            mock_get.return_value.raise_for_status = lambda: None

            response = self.client.get(self.url, {"code": "dummy_code"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["message"], "Kakao login successful")
            self.assertEqual(response.data["user"]["email"], "test@example.com")

            user = User.objects.get(email="test@example.com")
            social_user = SocialUser.objects.get(user=user)
            self.assertEqual(social_user.provider, SocialUser.ProviderChoices.KAKAO)
            self.assertEqual(social_user.provider_id, "12345")

    @patch("apps.users.services.social_user.requests.post")
    def test_invalid_code_or_api_failure(self, mock_post: Mock) -> None:
        mock_post.side_effect = Exception("카카오 API 호출 실패")

        response = self.client.get(self.url, {"code": "wrong_code"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("잘못된 요청", response.data["message"])

    @patch("apps.users.services.social_user.cache.set")
    def test_existing_user_login(self, mock_cache_set: Mock) -> None:
        user = User.objects.create(
            email="test@example.com",
            nickname="testuser",
            is_active=True,
            birthday="2000-01-01",
            name="testuser",
            phone_number="010-1234-5678",
            gender="male",
        )
        SocialUser.objects.create(
            user=user,
            provider=SocialUser.ProviderChoices.KAKAO,
            provider_id="12345",
        )

        with (
            patch("apps.users.services.social_user.requests.post") as mock_post,
            patch("apps.users.services.social_user.requests.get") as mock_get,
        ):
            mock_post.return_value.json.return_value = self.token_response
            mock_post.return_value.raise_for_status = lambda: None
            mock_get.return_value.json.return_value = self.user_response
            mock_get.return_value.raise_for_status = lambda: None

            response = self.client.get(self.url, {"code": "dummy_code"})

            if response.status_code == status.HTTP_400_BAD_REQUEST:
                print(response.data)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.data["is_new_user"])  # 신규 아님
            self.assertEqual(User.objects.filter(email="test@example.com").count(), 1)

    @patch("apps.users.services.social_user.cache.set")
    def test_cache_set_called(self, mock_cache_set: Mock) -> None:
        with (
            patch("apps.users.services.social_user.requests.post") as mock_post,
            patch("apps.users.services.social_user.requests.get") as mock_get,
        ):
            mock_post.return_value.json.return_value = self.token_response
            mock_post.return_value.raise_for_status = lambda: None
            mock_get.return_value.json.return_value = self.user_response
            mock_get.return_value.raise_for_status = lambda: None

            self.client.get(self.url, {"code": "dummy_code"})

            user = User.objects.get(email="test@example.com")
            mock_cache_set.assert_any_call(
                f"kakao_access_token:{user.id}",
                "fake_access_token",
                timeout=21599,
            )

    @patch("apps.users.services.social_user.requests.get")
    def test_user_info_missing_id(self, mock_get: Mock) -> None:
        mock_get.return_value.json.return_value = {"kakao_account": {"email": "test@example.com"}}
        mock_get.return_value.raise_for_status = lambda: None

        with patch("apps.users.services.social_user.requests.post") as mock_post:
            mock_post.return_value.json.return_value = self.token_response
            mock_post.return_value.raise_for_status = lambda: None

            response = self.client.get(self.url, {"code": "dummy_code"})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("잘못된 요청", response.data["message"])
