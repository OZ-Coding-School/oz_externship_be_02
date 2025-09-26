from typing import Any
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.tests.mixins.test_user_mixins import VerificationMixin
from apps.users.models import User
from apps.users.serializers.signup_serializers import UserSignupSerializer
from apps.users.services.exceptions import PhoneVerificationCodeFailedError
from apps.users.utils.enums import VerificationPurpose


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
        self.assertIn("email", serializer.data)


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

    @patch("apps.users.views.phone_verification_view.twilio_service.verify_service")
    def test_email_not_verified(self, mock_twilio_service: MagicMock) -> None:
        """
        이메일 인증번호 불일치 케이스
        """
        mock_twilio_service.verifications.create.return_value.status = "pending"
        mock_twilio_service.verification_checks.create.return_value.status = "approved"

        data = self._create_signup_data()
        email = data["email"]
        email_cache_key = f"{VerificationPurpose.SIGNUP.value}-{email}"
        # 이메일 인증
        self.client.post(reverse("email_send_code"), data={"email": email})
        email_verification_code = cache.get(email_cache_key)
        self.client.post(
            reverse("email_verify_code"), data={"email": email, "verification_code": str(email_verification_code)}
        )

        # 휴대폰 인증
        phone_number = data["phone_number"]
        self.client.post(reverse("phone_send_code"), data={"phone_number": phone_number})
        self.client.post(
            reverse("phone_verify_code"),
            data={"phone_number": phone_number, "verification_code": data["phone_verification_code"]},
        )

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("이메일 인증 코드가 올바르지 않거나 만료되었습니다.", response.data["error"])

    @patch("apps.users.serializers.signup_serializers.phone_service.is_verified")
    def test_phone_verification_code(self, mock_is_verified: MagicMock) -> None:
        """
        휴대폰 인증코드 불일치 케이스
        """
        data = self._create_signup_data()
        mock_is_verified.return_value = False

        response = self.client.post(self.url, self.signup_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_serializer_conflict_email(self) -> None:
        User.objects.create_user(
            email=self.signup_data["email"],
            password=self.signup_data["password"],
            nickname="existing",
            name="기존유저",
            phone_number="+821012345678",
            gender="F",
            birthday="2000-01-01"
        )
        # 1차 회원가입
        self.client.post(self.url, self.signup_data)
        # 2차 회원가입
        response = self.client.post(self.url, self.signup_data)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error", response.data)
        self.assertIn("email", response.data["error"])

    @patch("apps.users.serializers.signup_serializers.phone_service.is_verified")
    def test_signup_conflict_phone_number(self, mock_phone_verified: MagicMock) -> None:
        User.objects.create_user(
            email=self.signup_data["email"],
            password=self.signup_data["password"],
            nickname="existing",
            name="기존유저",
            phone_number= self.signup_data["phone_number"],
            gender="F",
            birthday="2000-01-01"
        )

        mock_phone_verified.return_value = True


        # 1차 회원가입
        response = self.client.post(self.url, self.signup_data)

        # 휴대폰 번호만 중복
        new_data = self._create_signup_data(email="test999@email.com")
        new_data["phone_number"] = self.signup_data["phone_number"]
        # 2차 회원가입
        response = self.client.post(self.url, new_data)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error", response.data)
        self.assertIn("phone_number", response.data["error"])