from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.tests.mixins.test_user_mixins import VerificationMixin
from apps.users.models.withdrawals import Withdrawals, WithdrawalsReasonChoices
from apps.users.services.email_service import EmailVerificationService
from apps.users.utils.enums import VerificationPurpose


class UserWithdrawalJWTAPITest(APITestCase, VerificationMixin):
    """
    회원 탈퇴 요청 API 테스트
    """

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


class UserRecoveryJWTAPITest(APITestCase, VerificationMixin):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = cls._create_test_user()  # 유저 생성

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)
        self.withdrawal_url = reverse("account_withdrawals")  # mypy 에러 방지용
        self.recovery_url = reverse("account_recovery")  # mypy 에러 방지용

    # * 인증 코드 설정
    def _set_verification_code(
        self,
        email: str,
        verification_code: str,
        purpose: VerificationPurpose = VerificationPurpose.RECOVER_ACCOUNT,
        timeout: int = 300,
    ) -> str:
        cache_key = f"{purpose.value}-{email}"
        cache.set(cache_key, verification_code, timeout=timeout)  # 5분 동안 유효
        return verification_code

    # * 탈퇴 복구
    @patch.object(EmailVerificationService, "is_verified", return_value=True)
    def test_account_recovery_request(self, mock_is_verified: MagicMock) -> None:
        # 1) 탈퇴 요청을 생성
        Withdrawals.objects.create(
            user=self.user,
            reason=WithdrawalsReasonChoices.PRIVACY_CONCERNS,
            reason_detail="개인정보/보안/우려",
            due_date=date.today() + timedelta(days=14),
        )

        # 이메일 발송 api 호출
        self.client.post(path=reverse("recover_account_send"), data={"email": self.user.email})
        cache_key = f"{VerificationPurpose.RECOVER_ACCOUNT.value}-{self.user.email}"
        verification_code = cache.get(cache_key)

        # 3) 탈퇴 신청 번복 (계정 복구 요청)
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
