import email

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from apps.core.tests.mixins.test_user_mixins import TestUserMixin
from apps.core.utils.test_clients import RedisTestClient
from apps.users.models import User
from apps.users.services.email_service import EmailVerificationService
from apps.users.utils.enums import VerificationPurpose


class EmailVerificationServiceUnitTests(TestCase):
    def setUp(self) -> None:
        self.service = EmailVerificationService()

    def test_generate_verification_code_func(self) -> None:
        verification_code = self.service.generate_verification_code()
        self.assertIsNotNone(verification_code)
        self.assertEqual(len(verification_code), 6)

    def test_send_verification_email_func(self) -> None:
        send_mail_count_before = len(mail.outbox)
        self.service.send_verification_email("test@example.com", purpose=VerificationPurpose.SIGNUP)
        self.assertEqual(len(mail.outbox), send_mail_count_before + 1)

    def test_verify_code_success_func(self) -> None:  # given
        email = "test@example.com"
        self.service.send_verification_email(email, purpose=VerificationPurpose.SIGNUP)
        verification_code = cache.get(f"{VerificationPurpose.SIGNUP}-{email}")
        # when
        result = self.service.verify_code(
            email, purpose=VerificationPurpose.SIGNUP, verification_code=verification_code
        )

        # then
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, {"detail": "인증이 완료되었습니다"})

    def test_verify_code_failed_func_when_code_is_wrong(self) -> None:  # given
        email = "test@example.com"
        verification_code = self.service.generate_verification_code()
        cache.set(email, verification_code)

        # when
        result = self.service.verify_code(email, purpose=VerificationPurpose.SIGNUP, verification_code="wrong")

        # then
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(result.data, {"error": "인증번호가 일치하지 않습니다"})


class EmailVerificationAPITest(RedisTestClient, TestUserMixin):
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = cls._create_test_user()

    def setUp(self) -> None:
        self.email_verication()

    def test_send_verification_email(self) -> None:
        # 이메일 인증요청에 사용할 이메일
        data = {"email": (email := self.email)}

        # 이메일 인증 요청 전송
        response = self.client.post(self.send_url, data)

        # 응답 상태코드 검증
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # mail.outbox에서 보낸 이메일의 제목이 전송된 이메일 제목과 같은지 검증
        self.assertEqual(mail.outbox[0].subject, "회원가입 이메일 인증")

        # 이메일 발송 시 사용한 인증번호를 캐시로 부터 가져오기
        verification_code = cache.get(f"{VerificationPurpose.SIGNUP}-{email}")

        # 인증번호가 캐시에 올바르게 저장되어 있었는지 검증
        self.assertIsNotNone(verification_code)
        # 인증번호가 메일에 올바르게 포함되어 전송되었는지 검증
        self.assertIn(verification_code, mail.outbox[0].body)

    def test_email_verify_code_sucess(self) -> None:
        # given
        # 이메일 인증요청에 사용할 이메일
        data = {"email": (email := self.email)}

        # 이메일 인증 이메일 전송 요청
        self.client.post(self.send_url, data)
        # 이메일 발송 시 사용한 인증번호를 캐시로 부터 가져오기
        verification_code = cache.get(f"{VerificationPurpose.SIGNUP.value}-{self.email}")

        response = self.client.post(self.verify_url, {"email": self.email, "verification_code": verification_code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(cache.get(email))

    def test_email_verify_code_failed(self) -> None:
        # given
        # 이메일 인증요청에 사용할 이메일
        data = {"email": self.email}

        # 이메일 인증 이메일 전송 요청
        self.client.post(self.send_url, data)

        response = self.client.post(self.verify_url, {"email": self.email, "verification_code": "wrong code"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetEmailVerificationAPITest(RedisTestClient, TestUserMixin):
    user: User
    """
    비밀번호 찾기 이메일 인증 테스틐 코드
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = cls._create_test_user()

    def setUp(self) -> None:
        self.email_reset_password()

    def test_send_verification_email(self) -> None:
        """
        비밀 번호 찾기 이메일 코드 전송
        """
        data = {"email": self.email}
        response = self.client.post(self.send_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mail.outbox[0].subject, "비밀번호 재설정 이메일 인증")
        cache_key = f"{VerificationPurpose.RESET_PASSWORD.value}-{self.email}"
        verification_code = cache.get(cache_key)
        self.assertIsNotNone(verification_code)

        response = self.client.post(self.verify_url, {"email": self.email, "code": verification_code})
        self.assertIn(verification_code, mail.outbox[0].body)

    def test_email_verify_code_success(self) -> None:
        """
        비밀번호 찾기 이메일 코드 검증
        :return:
        """
        data = {"email": self.email}
        self.client.post(self.send_url, data)

        cache_key = f"{VerificationPurpose.RESET_PASSWORD.value}-{self.email}"
        verification_code = cache.get(cache_key)

        self.assertIsNotNone(verification_code)

        response = self.client.post(self.verify_url, {"email": self.email, "verification_code": verification_code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(cache.get(cache_key))

    def test_email_verify_code_failed(self) -> None:
        """
        비밀번호 찾기 인증 실패 케이스
        """
        data = {"email": self.email}
        self.client.post(self.verify_url, data)

        response = self.client.post(self.verify_url, {"email": self.email, "code": "wrong"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AccountRecoveryEmailVerificationAPITest(RedisTestClient, TestUserMixin):
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = cls._create_test_user()

    def setUp(self) -> None:
        self.email_recover_account()

    def test_send_verification_email_success(self) -> None:
        """
        복구 이메일 인증 요청
        """
        response = self.client.post(self.send_url, {"email": self.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mail.outbox[0].subject, "탈퇴 계정 복구 이메일 인증")

        cache_key = f"{VerificationPurpose.RECOVER_ACCOUNT.value}-{self.email}"
        verification_code = cache.get(cache_key)
        self.assertIsNotNone(verification_code)

        response = self.client.post(self.verify_url, {"email": self.email, "verification_code": verification_code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(verification_code, mail.outbox[0].body)

    def test_email_verify_code_success(self) -> None:
        """
        계정 복구 이메인 인증 성공 케이스
        """
        self.client.post(self.send_url, {"email": self.email})

        cache_key = f"{VerificationPurpose.RECOVER_ACCOUNT.value}-{self.email}"
        verification_code = cache.get(cache_key)
        self.assertIsNotNone(verification_code)
        response = self.client.post(self.verify_url, {"email": self.email, "verification_code": verification_code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "인증이 완료되었습니다")
        self.assertTrue(cache.get(cache_key))

    def test_email_verify_code_failed(self) -> None:
        self.client.post(self.send_url, {"email": self.email})

        response = self.client.post(self.verify_url, {"email": self.email, "verification_code": "wrong"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "인증번호가 일치하지 않습니다")
