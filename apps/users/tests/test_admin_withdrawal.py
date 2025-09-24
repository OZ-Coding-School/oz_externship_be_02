from typing import ClassVar

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User, Withdrawals
from apps.users.utils.enums import Permission


class WithdrawalAdminAPITest(APITestCase):
    superuser: User
    staff_user: User
    general_user: User
    withdrawn_staff: User
    withdrawn_general: User
    list_url: ClassVar[str]

    @classmethod
    def setUpTestData(cls) -> None:
        """테스트에 필요한 모든 유저와 탈퇴 데이터를 직접 생성"""
        super().setUpTestData()

        cls.superuser = User.objects.create_superuser(
            email="superuser@test.com",
            password="pw",
            name="최고관리자",
            nickname="superuser",
            phone_number="010-0000-0000",
            birthday="1990-01-01",
            is_active=True,
        )
        cls.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="pw",
            name="스태프",
            nickname="staff",
            phone_number="010-1111-1111",
            birthday="1991-01-01",
            is_staff=True,
            is_active=True,
        )
        cls.general_user = User.objects.create_user(
            email="general@test.com",
            password="pw",
            name="일반유저",
            nickname="general",
            phone_number="010-2222-2222",
            birthday="1992-01-01",
            is_active=True,
        )
        cls.withdrawn_staff = User.objects.create_user(
            email="withdrawn_staff@test.com",
            password="pw",
            name="탈퇴스태프",
            nickname="w_staff",
            phone_number="010-3333-3333",
            birthday="1993-01-01",
            is_staff=True,
            is_active=True,
        )
        cls.withdrawn_general = User.objects.create_user(
            email="withdrawn_general@test.com",
            password="pw",
            name="탈퇴일반",
            nickname="w_general",
            phone_number="010-4444-4444",
            birthday="1994-01-01",
            is_active=True,
        )

        Withdrawals.objects.create(
            user=cls.withdrawn_staff, reason="OTHER", reason_detail="test", due_date="2025-01-01"
        )
        Withdrawals.objects.create(
            user=cls.withdrawn_general, reason="LACK_OF_INTEREST", reason_detail="test", due_date="2025-01-02"
        )

        cls.list_url = reverse("admin_user:admin-withdrawal-list")

    def test_list_withdrawals_success_as_admin(self) -> None:
        """관리자가 탈퇴 내역 목록을 성공적으로 조회하는지 테스트"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertNotIn("reason_detail", response.data["results"][0])

    def test_retrieve_withdrawal_detail_success(self) -> None:
        """관리자가 탈퇴 내역 상세 정보를 성공적으로 조회하는지 테스트"""
        self.client.force_authenticate(user=self.superuser)

        withdrawal_obj = Withdrawals.objects.get(user=self.withdrawn_staff)
        detail_url = reverse("admin_user:admin-withdrawal-detail", kwargs={"pk": withdrawal_obj.pk})

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("reason_detail", response.data)
        self.assertEqual(response.data["email"], self.withdrawn_staff.email)

    def test_list_withdrawals_fail_for_general_user(self) -> None:
        """일반 유저가 탈퇴 내역 조회 시 403 에러가 발생하는지 테스트"""
        self.client.force_authenticate(user=self.general_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_withdrawal_list_features(self) -> None:
        """탈퇴 내역 목록의 필터링, 검색, 정렬 기능 테스트"""
        self.client.force_authenticate(user=self.superuser)

        # 권한(staff)으로 필터링
        response = self.client.get(self.list_url, {"permission": Permission.STAFF.name})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], self.withdrawn_staff.email)

        # 이메일로 검색
        response = self.client.get(self.list_url, {"search": "w_general"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], "withdrawn_general@test.com")

        # 탈퇴 요청일(created_at) 오름차순 정렬
        response = self.client.get(self.list_url, {"ordering": "created_at"})
        self.assertEqual(response.data["results"][0]["email"], self.withdrawn_staff.email)

    def test_restore_user_success_as_admin(self) -> None:
        """탈퇴 유저 신청한 유저 복구 테스트"""
        # 관리자 권한 유저 복구 기능 테스트
        self.client.force_authenticate(user=self.superuser)

        # 복구 대상으로 지정할 객체
        withdrawal_obj = Withdrawals.objects.get(user=self.withdrawn_staff)

        # restore에 대한 URL 생성
        restore_url = reverse("admin_user:admin-withdrawal-restore", kwargs={"pk": withdrawal_obj.pk})

        # POST 요청 실행
        response = self.client.post(restore_url)

        # 1. 성공 응답
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "유저 복구가 완료 되었습니다.")

        # 2. Withdrawals 테이블에서 해당 유저 삭제 여부 확인
        self.assertFalse(Withdrawals.objects.filter(pk=withdrawal_obj.pk).exists())
        self.withdrawn_staff.refresh_from_db()
        self.assertTrue(self.withdrawn_staff.is_active)

    def test_restore_user_success_as_staff(self) -> None:
        # 스태프 권한 유저 복구 기능 테스트
        self.client.force_authenticate(user=self.staff_user)

        # 복구 대상으로 지정할 객체
        withdrawal_obj = Withdrawals.objects.get(user=self.withdrawn_staff)

        # restore에 대한 URL 생성
        restore_url = reverse("admin_user:admin-withdrawal-restore", kwargs={"pk": withdrawal_obj.pk})

        # POST 요청 실행
        response = self.client.post(restore_url)

        # 1. 성공 응답
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. Withdrawals 테이블에서 해당 유저 삭제 여부 확인
        self.assertFalse(Withdrawals.objects.filter(pk=withdrawal_obj.pk).exists())

        # 3. User 모델의 is_active 상태 True 변경 여부 확인
        self.withdrawn_staff.refresh_from_db()
        self.assertTrue(self.withdrawn_staff.is_active)

    def test_restore_user_fail_for_general_user(self) -> None:
        """권한이 없는 유저가 복구 시도시 403 에러 반환 테스트"""
        self.client.force_authenticate(user=self.general_user)

        withdrawal_obj = Withdrawals.objects.get(user=self.withdrawn_staff)
        restore_url = reverse("admin_user:admin-withdrawal-restore", kwargs={"pk": withdrawal_obj.pk})

        response = self.client.post(restore_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
