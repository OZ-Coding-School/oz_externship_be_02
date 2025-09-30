# apps/users/tests/test_reset_password.py

from datetime import date
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models.user import User
from apps.users.serializers.reset_password_serializer import email_verify
from apps.users.services.email_service import EmailVerificationService
from apps.users.utils.enums import VerificationPurpose


class ResetPasswordAPITest(APITestCase):
    user: User
    verification_code: str
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        # 테스트용 기본 사용자 생성
        cls.user = User.objects.create_user(
            profile_img_url="http://example.com/profile.jpg",
            email="test@example.com",
            password="securepassword123",
            nickname="cooluser",
            name="Imsocool",
            phone_number="01012345678",
            birthday=date(2001, 9, 22),
            is_active=True,
        )

        cls.url = reverse("reset_password")

    def setUp(self) -> None:

        self.verification_code = "123456"  # 테스트용 인증 코드
        cache_key = f"{VerificationPurpose.RESET_PASSWORD.value}-{self.user.email}"
        cache.set(cache_key, self.verification_code, timeout=600)

    @patch.object(email_verify, "verify_code", return_value=True)
    def test_reset_password_success(self, mock_verify: MagicMock) -> None:

        data = {"email": self.user.email, "verification_code": self.verification_code, "new_password": "NewPassword123"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword123"))

    def test_reset_password_invalid_code(self) -> None:
        data = {
            "email": self.user.email,
            "verification_code": "234561",  # 잘못된 코드
            "new_password": "NewPassword123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
