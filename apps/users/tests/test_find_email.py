# apps/users/tests/test_find_email.py

from datetime import date
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.utils import RedisTestClient
from apps.users.models import User
from apps.users.serializers import find_email_serializer
from apps.users.services.exceptions import PhoneVerificationCodeFailedError
from apps.users.utils.enums import VerificationPurpose


class EmailRecoveryTestCase(RedisTestClient):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(  # type: ignore
            profile_img_url="http://example.com/profile.jpg",
            email="test@example.com",
            password="securepassword123",
            nickname="cooluser",
            name="Imsocool",
            phone_number="+82 1012345678",
            birthday=date(2001, 9, 22),
            is_active=True,
        )
        cls.find_email_url = reverse("find_email")
        cls.send_code_url = reverse("find_email_send_code")
        cls.verify_url = reverse("find_email_verify_code")
        cls.code = "123456"

    def setUp(self):
        self.client = self.client_class()

    @patch("apps.users.views.phone_verification_view.twilio_service")
    def test_email_recovery_success(self, mock_twilio_service: MagicMock):
        # 인증 성공
        mock_twilio_service.send_verification_code.return_value = None
        mock_twilio_service.check_verification_code.return_value = None

        code = "123456"

        send_code_response = self.client.post(self.send_code_url, data={"phone_number": self.user.phone_number})
        self.assertEqual(send_code_response.status_code, status.HTTP_200_OK)

        verify_code_response = self.client.post(
            self.verify_url, data={"phone_number": self.user.phone_number, "verification_code": code}
        )
        self.assertEqual(verify_code_response.status_code, status.HTTP_200_OK)

        cache_key = f"{VerificationPurpose.FIND_EMAIL.value}-verified-{self.user.phone_number}"
        cache.set(cache_key, code, timeout=600)

        response = self.client.post(
            self.find_email_url,
            data={"name": self.user.name, "phone_number": self.user.phone_number, "code": code},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    #! 여기가 문제
    @patch.object(find_email_serializer.phone_service, "check_verification_code")
    def test_email_recovery_invalid_code(self, mock_check):
        # 인증 실패 강제 발생
        mock_check.side_effect = PhoneVerificationCodeFailedError("인증 실패")
        data = {"name": self.user.name, "phone_number": self.user.phone_number, "code": "234852"}
        response = self.client.post(self.url, data, format="json")
        print("응답 상태 코드:", response.status_code)
        print("응답 내용:", response.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)
        mock_check.assert_called_once()

    @patch.object(find_email_serializer.phone_service, "check_verification_code")
    def test_email_recovery_user_not_found(self, mock_check):
        # 사용자 없음, 인증은 성공
        mock_check.return_value = None

        verified_key = f"{VerificationPurpose.FIND_EMAIL.value}-verified-01099999999"
        cache.set(verified_key, "123456", timeout=600)

        data = {"name": "Nobody", "phone_number": "01099999999", "code": "123456"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        mock_check.assert_called_once()

    @patch.object(find_email_serializer.phone_service, "check_verification_code")
    def test_email_recovery_missing_fields(self, mock_check):
        # 필수 입력값 누락 (code 빈칸)
        mock_check.return_value = None

        data = {"name": self.user.name, "phone_number": self.user.phone_number, "code": ""}  # 누락
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        mock_check.assert_not_called()
