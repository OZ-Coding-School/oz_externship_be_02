from apps.users.models.user import User


class TestUserMixin:
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
