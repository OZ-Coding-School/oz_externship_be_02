from typing import Any, Dict
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.tests.mixins.test_user_mixins import TestUserMixin, VerificationMixin
from apps.users.models import User
from apps.users.services.exceptions import (
    PhoneSendingFailedError,
    PhoneVerificationCodeFailedError,
)
from apps.users.views.phone_verification_view import twilio_service


class PhoneVerificationTests(APITestCase, VerificationMixin):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.phone_number = "+821012345678"
        cls.verification_code = "123456"
        cls.user = cls._create_test_user()
        urls = cls.get_phone_verification_urls()
        cls.send_url = urls["send_url"]
        cls.verify_url = urls["verify_url"]

    @patch("apps.users.views.phone_verification_view.twilio_service.send_verification_code")
    def test_send_verification_code_success(self, mock_send: MagicMock) -> None:
        """
        휴대폰 인증번호 전송 성공 케이스
        """
        mock_send.return_value = None

        data = {"phone_number": "01012345678"}
        response = self.client.post(self.send_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertIn(response.data["detail"], "휴대폰 인증번호가 전송되었습니다")

    @patch("apps.users.views.phone_verification_view.twilio_service.send_verification_code")
    def test_send_verification_code_fail(self, mock_send: MagicMock) -> None:
        """
        휴대폰 인증번호 전송 실패 케이스
        """
        mock_send.side_effect = PhoneSendingFailedError("인증번호 전송에 실패했습니다")

        data = {"phone_number": "invalid_numbers"}
        response = self.client.post(self.send_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "인증번호 전송에 실패했습니다")

    @patch("apps.users.views.phone_verification_view.twilio_service.check_verification_code")
    def test_check_verification_code_success(self, mock_check: MagicMock) -> None:
        mock_check.return_value = None

        data = {"phone_number": self.phone_number, "verification_code": self.verification_code}
        response = self.client.post(self.verify_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    @patch("apps.users.views.phone_verification_view.twilio_service.verify_service")
    def test_check_verification_code_fail(self, mock_check: MagicMock) -> None:
        mock_check.verification_checks.create.return_value.status = "failed"

        data = {"phone_number": self.phone_number, "verification_code": "12345."}
        response = self.client.post(self.verify_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "휴대폰 인증번호가 일치하지 않습니다")
