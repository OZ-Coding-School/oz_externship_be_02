from datetime import date, timedelta

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.tests.mixins.test_user_mixins import (
    IsolatedCacheTestMixin,
    TestUserMixin,
)
from apps.users.models import User
from apps.users.models.withdrawals import Withdrawals, WithdrawalsReasonChoices
from apps.users.utils.enums import VerificationPurpose


class UserWithdrawalJWTAPITest(APITestCase, IsolatedCacheTestMixin, TestUserMixin):
    """
    회원 탈퇴 요청 API 테스트
    """

    user: User
    url: str

    @classmethod
    # 클래스 메소드: 테스트 클래스 전체에서 공유하는 데이터 설정
    def setUpTestData(cls) -> None:
        cls.user = cls._create_test_user()  # 유저 생성
        cls.url = reverse("account_withdrawals")  # mypy 에러 방지용

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_successful_withdrawal_request(self) -> None:
        data = {
            "reason": WithdrawalsReasonChoices.PRIVACY_CONCERNS,
            "reason_detail": "개인정보/보안/우려",
        }  # 요청 데이터
        response = self.client.delete(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        withdrawal = Withdrawals.objects.filter(user=self.user).first()
        assert withdrawal is not None
        self.assertIsNotNone(withdrawal)
        self.assertEqual(
            withdrawal.reason,
            WithdrawalsReasonChoices.PRIVACY_CONCERNS,
        )
        self.assertEqual(withdrawal.reason_detail, "개인정보/보안/우려")

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_duplicate_withdrawal_request(self) -> None:
        # 첫 번째 탈퇴 요청(정상적)
        first_data = {
            "reason": WithdrawalsReasonChoices.PRIVACY_CONCERNS,
            "reason_detail": "첫 요청",
        }
        first_response = self.client.delete(self.url, first_data)
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        # 두 번째 중복 요청(비정상적)
        second_data = {
            "reason": WithdrawalsReasonChoices.PRIVACY_CONCERNS,
            "reason_detail": "테스트용 중복 요청",
        }
        second_response = self.client.delete(self.url, second_data)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("error", second_response.data)
        self.assertIn("이미 탈퇴 요청이 존재합니다", second_response.data["error"])


class UserRecoveryJWTAPITest(APITestCase, TestUserMixin, IsolatedCacheTestMixin):
    user: User
    withdrawal_url: str
    recovery_url: str
    recovery_send_url: str
    verify_url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = cls._create_test_user()  # 유저 생성
        cls.withdrawal_url = reverse("account_withdrawals")
        cls.recovery_url = reverse("account_recovery")
        cls.recovery_send_url = reverse("recover_account_send")
        cls.verify_url = reverse("recover_account_verify")

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_account_recovery_request(self) -> None:
        # 1) 탈퇴 요청을 생성
        Withdrawals.objects.create(
            user=self.user,
            reason=WithdrawalsReasonChoices.PRIVACY_CONCERNS,
            reason_detail="개인정보/보안/우려",
            due_date=date.today() + timedelta(days=14),
        )

        # 이메일 발송 api 호출
        send_response = self.client.post(path=reverse("recover_account_send"), data={"email": self.user.email})
        self.assertEqual(send_response.status_code, status.HTTP_200_OK)

        cache_key = f"{VerificationPurpose.RECOVER_ACCOUNT.value}-{self.user.email}"
        verification_code = str(cache.get(cache_key))

        # 이메일 인증 api 호출
        verify_response = self.client.post(
            path=self.verify_url, data={"email": self.user.email, "verification_code": verification_code}
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        # 회원 계정 복구 api 호출
        data = {
            "email": self.user.email,
            "verification_code": verification_code,
        }

        response = self.client.post(self.recovery_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "계정이 복구되었습니다. 이제 로그인할 수 있습니다.")

        # 4) 유저 계정 활성화 확인
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        # 5) Withdrawals 레코드에서 해당 유저가 삭제되었는지 확인
        self.assertFalse(Withdrawals.objects.filter(user=self.user).exists())

    def test_account_recovery_request_fail_when_user_invalid_code(self) -> None:
        # 1) 탈퇴 요청을 생성
        Withdrawals.objects.create(
            user=self.user,
            reason=WithdrawalsReasonChoices.PRIVACY_CONCERNS,
            reason_detail="개인정보/보안/우려",
            due_date=date.today() + timedelta(days=14),
        )

        # 회원 계정 복구 api 호출
        data = {
            "email": self.user.email,
            "verification_code": "nvalid",
        }

        response = self.client.post(self.recovery_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
