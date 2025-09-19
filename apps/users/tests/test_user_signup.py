from typing import Any
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.tests.mixins.test_user_mixins import VerificationMixin
from apps.users.models import User
from apps.users.serializers.signup_serializers import UserSignupSerializer
from apps.users.services.exceptions import PhoneVerificationCodeFailedError


class UserSignupTestCase(APITestCase, VerificationMixin):
    @classmethod
    def _create_signup_data(cls, **kwargs: Any) -> dict[str, Any]:
        defaults = {
            "email": "newuser1@email.com",
            "password": "testpassword",
            "name": "신규유저",
            "nickname": "newuser",
            "phone_number": "+821027593041",
            "gender": "F",
            "birthday": "2000-01-02",
            "email_verification_code": "123456",
            "phone_verification_code": "654321",
        }
        defaults.update(kwargs)
        return defaults

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("signup")
        cls.signup_data = cls._create_signup_data()

    @patch("apps.users.serializers.signup_serializers.email_service.is_verified")
    @patch("apps.users.serializers.signup_serializers.phone_service.is_verified")
    def test_user_signup(self, mock_phone_verified: MagicMock, mock_email_verified: MagicMock) -> None:
        """
        회원가입 성공 케이스
        """
        mock_phone_verified.return_value = True
        mock_email_verified.return_value = True

        serializer = UserSignupSerializer(data=self.signup_data)
        is_valid = serializer.is_valid()

        self.assertTrue(is_valid, "serializer validation failed")

        response = self.client.post(self.url, self.signup_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)


class UserSignupFailureTestCase(APITestCase, VerificationMixin):

    @classmethod
    def _create_signup_data(cls, **kwargs: Any) -> dict[str, Any]:
        defaults = {
            "email": "newuser1@email.com",
            "password": "testpassword",
            "name": "신규유저",
            "nickname": "newuser",
            "phone_number": "+821027593041",
            "gender": "F",
            "birthday": "2000-01-02",
            "email_verification_code": "123456",
            "phone_verification_code": "654321",
        }
        defaults.update(kwargs)
        return defaults

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("signup")
        cls.signup_data = cls._create_signup_data()

    @patch("apps.users.serializers.signup_serializers.email_service.is_verified")
    def test_email_not_verified(self, mock_is_verified: MagicMock) -> None:
        """
        이메일 인증번호 불일치 케이스
        """
        data = self._create_signup_data()
        mock_is_verified.return_value = False

        response = self.client.post(self.url, self.signup_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email_verification_code", response.data)

    @patch("apps.users.serializers.signup_serializers.phone_service.is_verified")
    def test_phone_verification_code(self, mock_is_verified: MagicMock) -> None:
        """
        휴대폰 인증코드 불일치 케이스
        """
        data = self._create_signup_data()
        mock_is_verified.return_value = False

        response = self.client.post(self.url, self.signup_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_verification_code", response.data)
