# users/tests/test_withdrawals.py

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.tests.mixins.test_user_mixins import TestUserMixin
from apps.users.models.withdrawals import Withdrawals


class UserWithdrawalJWTAPITest(APITestCase, TestUserMixin):
    def setUp(self) -> None:
        self.user = self._create_test_user()
        self.url = reverse("account_withdrawals")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_successful_withdrawal_request(self) -> None:
        data = {"reason": "PRIVACY_CONCERNS", "reason_detail": "개인정보/보안/우려", "due_date": "2025-09-08"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        withdrawal = Withdrawals.objects.filter(user=self.user).first()
        assert withdrawal is not None
        self.assertIsNotNone(withdrawal)
        self.assertEqual(withdrawal.reason, "PRIVACY_CONCERNS")
        self.assertEqual(withdrawal.reason_detail, "개인정보/보안/우려")

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    # 이미 탈퇴 요청한 사용자: 중복 요청
    def test_duplicate_withdrawal_request(self) -> None:
        first_data = {"reason": "PRIVACY_CONCERNS", "reason_detail": "첫 요청", "due_date": "2025-09-08"}
        first_response = self.client.post(self.url, first_data)
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        second_data = {"reason": "PRIVACY_CONCERNS", "reason_detail": "테스트용 중복 요청", "due_date": "2025-09-08"}
        second_response = self.client.post(self.url, second_data)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(second_response.data["error"], "이미 탈퇴 요청이 존재합니다.")
