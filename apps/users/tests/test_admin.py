from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.tests.mixins.test_user_mixins import TestUserMixin
from apps.users.models import User, Withdrawals

user_model = User


class UserAdminAPITest(APITestCase, TestUserMixin):
    superuser: "User"
    staff_user: "User"

    # Mixin을 사용하지 않고 모든 유저를 직접 생성하여 고유성을 보장합니다.
    @classmethod
    def setUpTestData(cls) -> None:
        cls.superuser = user_model.objects.create_superuser(
            email="superuser@test.com",
            password="pw",
            name="최고관리자",
            nickname="superuser",
            phone_number="010-0000-0000",
            birthday="1990-01-01",
            is_active=True,
        )
        cls.staff_user = user_model.objects.create_user(
            email="staff@test.com",
            password="pw",
            name="스태프",
            nickname="staff",
            phone_number="010-1111-1111",
            birthday="1991-01-01",
            is_staff=True,
            is_active=True,
        )

    def setUp(self) -> None:
        self.active_user = user_model.objects.create_user(
            email="active@test.com",
            password="pw",
            name="활성유저",
            nickname="active_us",
            phone_number="010-2222-2222",
            birthday="1992-01-01",
            is_active=True,
        )
        # self.inactive_user = user_model.objects.create_user(
        #     email="inactive@test.com",
        #     password="pw",
        #     name="비활성유저",
        #     nickname="inactive",
        #     phone_number="010-3333-3333",
        #     birthday="1993-01-01",
        #     is_active=False,
        # )
        # self.withdrawn_user = user_model.objects.create_user(
        #     email="withdrawn@test.com",
        #     password="pw",
        #     name="탈퇴유저",
        #     nickname="withdrawn",
        #     phone_number="010-4444-4444",
        #     birthday="1994-01-01",
        #     is_active=True,
        # )

        # Withdrawals.objects.create(
        #     user=self.withdrawn_user, reason="OTHER", reason_detail="test", due_date="2025-12-31"
        # )
        # self.list_url = reverse("admin_user:users-list")

    # 권한 수정 API 테스트
    # 슈퍼유저가 일반유저의 권한을 staff으로 변경하는 기능 테스트
    def test_permission_update_success_as_superuser(self) -> None:
        self.client.force_authenticate(user=self.superuser)
        data = {"permission": "staff"}
        url = reverse("admin_user:user_permissions", kwargs={"user_uuid": self.active_user.uuid})

        response = self.client.patch(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_user.refresh_from_db()
        self.assertTrue(self.active_user.is_staff)
        self.assertFalse(self.active_user.is_superuser)

    # 일반 스태프가 권한 변경 시도 시 403 에러가 발생하는지 테스트
    def test_permission_update_fail_as_staff(self) -> None:
        self.client.force_authenticate(user=self.staff_user)
        data = {"permission": "admin"}
        url = reverse("admin_user:user_permissions", kwargs={"user_uuid": self.active_user.uuid})
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
