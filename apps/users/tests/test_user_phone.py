from typing import Any, Dict
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class PhoneVerificationTests(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.send_url = reverse("phone_send_code")
        self.verify_url = reverse("phone_verify_code")

    @patch("apps.users.services.phone_service.TwilioAuthService.send_verification_code")
    def test_send_verification_code_success(self, mock_send: MagicMock) -> None:
        mock_send.return_value = {"success": True, "message": "인증번호 전송 완료"}

        data = {"phone_number": "01012345678"}
        response = self.client.post(self.send_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertIn(response.data["detail"], "인증번호가 전송되었습니다")

    @patch("apps.users.services.phone_service.TwilioAuthService.send_verification_code")
    def test_send_verification_code_fail(self, mock_send: MagicMock) -> None:
        mock_send.return_value = {"success": False, "message": "invalid_number"}

        data = {"phone_number": "invalid_number"}
        response = self.client.post(self.send_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "인증번호 전송에 실패했습니다")
