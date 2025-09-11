from django.urls import reverse

from apps.users.models.user import User


class TestUserMixin:
    @classmethod
    def _create_test_user(self, email: str = "test@example.com") -> User:
        return User.objects.create_user(
            email=email,
            password="testpassword",
            name="테스트유저",
            nickname="tester",
            phone_number="01012345678",
            gender="M",
            birthday="2000-01-01",
        )

    def email_recover_account(self) -> None:
        self.email ="recover@test.com"
        self.send_url = reverse("recover_account_send")
        self.verify_url = reverse("recover_account_verify")

    def email_reset_password(self) ->None:
        self.email = "password@example.com"
        self.send_url = reverse("password_reset_send")
        self.verify_url = reverse("password_reset_verify")

    def email_verication(self) ->None:
        self.email = "email@example.com"
        self.send_url = reverse("email_send_code")
        self.verify_url = reverse("email_verify_code")

    def phone_verification(self) ->None:
        self.send_url = reverse("phone_send_code")
        self.verify_url = reverse("phone_verify_code")
