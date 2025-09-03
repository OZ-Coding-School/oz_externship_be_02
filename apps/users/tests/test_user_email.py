from django.core import mail
from django.core.mail import send_mail
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from apps.users.services.auth_service import generate_verification_code, verify_user_email
from apps.users.models import User
from django.core.cache import cache

class EmailVerificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.email = "test@example.com"

    def test_generate_verification_code(self):
        verification_code = generate_verification_code(self.email)
        self.assertIsNotNone(verification_code)
        self.assertEqual(len(verification_code), 12)
        cached_code = cache.get(self.email)
        self.assertEqual(cached_code, verification_code)

    def test_verify_user_email_success(self):
        verification_code = generate_verification_code(self.email)
        user = User.objects.create_user(
            email=self.email,
            password='testpassword',
            name='테스트유저',
            nickname='tester',
            phone_number='01012345678',
            gender='M',
            birthday='2000-01-01'
        )
        verified_user = verify_user_email(self.email, verification_code)
        cache.clear()
        self.assertTrue(verified_user.is_active)
        self.assertIsNone(cache.get(self.email))

    def test_verify_user_email_invalid_email(self):
        with self.assertRaises(ValidationError) as context:
            verify_user_email("invalid@example.com", "testcode")
        self.assertEqual(str(context.exception.detail[0]), "존재하지않는 이메일입니다")

    def test_verify_user_email_invalid_verification_code(self):
        verification_code = generate_verification_code(self.email)
        user = User.objects.create_user(
            email=self.email,
            password='testpassword',
            name='테스트유저',
            nickname='tester',
            phone_number='01012345678',
            gender='M',
            birthday='2000-01-01'
        )
        with self.assertRaises(ValidationError) as context:
            verify_user_email(self.email, 'invalidcode')
        self.assertEqual(str(context.exception.detail[0]), "인증코드가 일치하지않습니다")

    def test_send_verification_email(self):
        send_mail_count_before = len(mail.outbox)
        send_mail(
            "Subject here",
            "메세지 발송",
            "from@example.com",
            ["to@example.com"],
            fail_silently=False,
        )
        self.assertEqual(len(mail.outbox), send_mail_count_before + 1)

class VerificationCodeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.email = "test@example.com"
        self.verification_code = generate_verification_code(self.email)
        self.user = User.objects.create_user(
            email=self.email,
            password='testpassword',
            name='테스트유저',
            nickname='tester',
            phone_number='01012345678',
            gender='M',
            birthday='2000-01-01'
        )
        self.verification_url = reverse('verify_email')

    def test_verification_view_success(self):
        data = {'email': self.email, 'verification_code': self.verification_code}
        response = self.client.post(self.verification_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '이메일 인증 성공')
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_verification_view_invalid_data(self):
        data = {'email': self.email,'verification_code': 'wrong_code'}
        response = self.client.post(self.verification_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
