from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User, Withdrawals
from apps.users.utils.enums import Permission, UserStatus

user_model = User


class UserAdminAPITest(APITestCase):
    superuser: User
    staff_user: User
    active_user: User
    inactive_user: User
    withdrawn_user: User
    list_url: str

    @classmethod
    def setUpTestData(cls) -> None:
        """모든 테스트 유저를 여기서 직접 생성해서 고유성 보장"""
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
            nickname="staff_user",
            phone_number="010-1111-1111",
            birthday="1991-01-01",
            is_staff=True,
            is_active=True,
        )
        cls.active_user = user_model.objects.create_user(
            email="active@test.com",
            password="pw",
            name="활성유저",
            nickname="active_us",
            phone_number="010-2222-2222",
            birthday="1992-01-01",
            is_active=True,
        )
        cls.inactive_user = user_model.objects.create_user(
            email="inactive@test.com",
            password="pw",
            name="비활성유저",
            nickname="inactive",
            phone_number="010-3333-3333",
            birthday="1993-01-01",
            is_active=False,
        )
        cls.withdrawn_user = user_model.objects.create_user(
            email="withdrawn@test.com",
            password="pw",
            name="탈퇴유저",
            nickname="withdrawn",
            phone_number="010-4444-4444",
            birthday="1994-01-01",
            is_active=True,
        )

        Withdrawals.objects.create(user=cls.withdrawn_user, reason="OTHER", reason_detail="test", due_date="2025-12-31")
        cls.list_url = reverse("admin_user:users-list")

    # 권한 수정 API 테스트
    def test_permission_update_success_as_superuser(self) -> None:
        self.client.force_authenticate(user=self.superuser)
        data = {"permission": Permission.STAFF.value[0]}
        url = reverse("admin_user:user_permissions", kwargs={"user_uuid": self.active_user.uuid})
        response = self.client.patch(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_user.refresh_from_db()
        self.assertTrue(self.active_user.is_staff)

    def test_permission_update_fail_as_staff(self) -> None:
        self.client.force_authenticate(user=self.staff_user)
        data = {"permission": Permission.ADMIN.value[0]}
        url = reverse("admin_user:user_permissions", kwargs={"user_uuid": self.active_user.uuid})
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 회원 목록 및 상세 조회 API 테스트
    def test_list_and_retrieve_users_success_as_staff(self) -> None:
        """슈퍼유저가 아닌 일반 스태프가 회원 목록과 상세 정보를 성공적으로 조회하는지 테스트"""
        self.client.force_authenticate(user=self.staff_user)

        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        detail_url = reverse("admin_user:users-detail", kwargs={"uuid": self.active_user.uuid})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertIn("phone_number", detail_response.data)

    def test_access_denied_for_general_user(self) -> None:
        """일반 유저가 관리자 API 접근 시 403 에러가 발생하는지 테스트"""
        self.client.force_authenticate(user=self.active_user)

        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)

        detail_url = reverse("admin_user:users-detail", kwargs={"uuid": self.staff_user.uuid})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_403_FORBIDDEN)

    # 필터링, 검색, 정렬 테스트
    def test_list_features_work_correctly(self) -> None:
        """목록 조회의 필터링, 검색, 정렬 기능이 올바르게 동작하는지 테스트"""
        self.client.force_authenticate(user=self.superuser)

        # 권한 필터링 테스트
        permission_response = self.client.get(self.list_url, {"permission": Permission.STAFF.value[0]})
        self.assertEqual(permission_response.data["count"], 1)
        self.assertEqual(permission_response.data["results"][0]["email"], self.staff_user.email)

        # 필터링 기능 테스트
        response = self.client.get(self.list_url, {"status": UserStatus.WITHDRAWN.value[0]})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], self.withdrawn_user.email)

        # 검색 기능 테스트
        response = self.client.get(self.list_url, {"search": "active_us"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], self.active_user.email)

        # 정렬 기능 테스트
        response = self.client.get(self.list_url, {"ordering": "-created_at"})
        self.assertEqual(response.data["results"][0]["email"], self.withdrawn_user.email)

    # 회원 정보 수정 API 테스트
    def test_user_update_success_as_admin(self) -> None:
        """관리자 권한을 가진 유저가 다른 유저의 정보 수정 테스트"""
        self.client.force_authenticate(user=self.superuser)

        detail_url = reverse("admin_user:users-detail", kwargs={"uuid": self.active_user.uuid})
        data = {"nickname": "changed_us", "status": "inactive"}
        response = self.client.patch(detail_url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.active_user.refresh_from_db()
        self.assertEqual(self.active_user.nickname, "changed_us")
        self.assertFalse(self.active_user.is_active)

    def test_user_update_fail_as_staff(self) -> None:
        """스태프 권한을 가진 유저가 다른 유저의 정보 수정 테스트"""
        self.client.force_authenticate(user=self.staff_user)

        detail_url = reverse("admin_user:users-detail", kwargs={"uuid": self.active_user.uuid})
        data = {"nickname": "changed_sf"}
        response = self.client.patch(detail_url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.active_user.refresh_from_db()
        self.assertEqual(self.active_user.nickname, "changed_sf")

    def test_user_update_fail_for_general_staff(self) -> None:
        """권한이 없는 유저가 다른 유저 정보 수정시 403 에러 발생 여부 테스트"""
        self.client.force_authenticate(user=self.active_user)
        detail_url = reverse("admin_user:users-detail", kwargs={"uuid": self.active_user.uuid})
        data = {"nickname": "hacked"}

        responses = self.client.patch(detail_url, data=data, format="json")
        self.assertEqual(responses.status_code, status.HTTP_403_FORBIDDEN)

    # 회원 정보 삭제 테스트
    def test_delete_user_success_as_superuser(self) -> None:
        """관리자(superuser)권한 유저가 다른 유저 정보를 삭제하는 테스트"""
        self.client.force_authenticate(user=self.superuser)

        target_user_uuid = self.active_user.uuid
        detail_url = reverse("admin_user:users-detail", kwargs={"uuid": target_user_uuid})

        responses = self.client.delete(detail_url)

        self.assertEqual(responses.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(user_model.DoesNotExist):
            user_model.objects.get(uuid=target_user_uuid)

    def test_delete_user_fail_as_staff(self) -> None:
        """스태프(staff)권한 유저가 다른 유저 정보를 삭제하는 테스트"""
        self.client.force_authenticate(user=self.staff_user)
        detail_url = reverse("admin_user:users-detail", kwargs={"uuid": self.active_user.uuid})

        responses = self.client.delete(detail_url)

        self.assertEqual(responses.status_code, status.HTTP_403_FORBIDDEN)
