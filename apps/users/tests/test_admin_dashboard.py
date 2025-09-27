from datetime import date
from typing import ClassVar

from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Faker
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User, Withdrawals, WithdrawalsReasonChoices

user_model = get_user_model()
fake = Faker("ko_KR")


class AdminDashboardAPITest(APITestCase):
    superuser: User
    staff_user: User
    general_user: User
    signup_url: ClassVar[str]
    withdrawal_url: ClassVar[str]
    withdrawal_reason_url: ClassVar[str]

    @classmethod
    def setUpTestData(cls) -> None:
        """테스트에서 사용할 유저데이터 생성"""
        super().setUpTestData()

        # 1. 테스트에 필요한 관리자 및 일반 유저 데이터 생성
        with freeze_time("2025-10-01"):
            cls.superuser = user_model.objects.create_superuser(
                email="superuser@test.com",
                password="pw",
                name="슈퍼유저",
                nickname="superuser",
                phone_number=fake.unique.phone_number(),
                birthday=fake.date_of_birth(minimum_age=20, maximum_age=40),
                gender="M",
            )

            cls.staff_user = user_model.objects.create_user(
                email="staff@test.com",
                password="pw",
                name="스태프",
                nickname="staff",
                phone_number=fake.unique.phone_number(),
                birthday=fake.date_of_birth(minimum_age=20, maximum_age=40),
                gender="M",
                is_staff=True,
            )

            cls.general_user = user_model.objects.create_user(
                email="general@test.com",
                password="pw",
                name="일반유저",
                nickname="general",
                phone_number=fake.unique.phone_number(),
                birthday=fake.date_of_birth(minimum_age=20, maximum_age=40),
                gender="M",
            )

        # 2. freezegun 라이브러리를 사용해 특정 시간에 데이터를 생성
        with freeze_time("2023-09-10"):
            # 23년도에 가입한 유저 1명
            user_model.objects.create_user(
                email=fake.unique.email(),
                password="pw",
                name=fake.name(),
                nickname=fake.pystr(max_chars=10),
                phone_number=fake.unique.phone_number(),
                birthday=fake.date_of_birth(),
                gender="M",
            )

        with freeze_time("2025-08-21"):
            # 24년도 5월 가입한 유저 2명
            user_model.objects.create_user(
                email=fake.unique.email(),
                password="pw",
                name=fake.name(),
                nickname=fake.pystr(max_chars=10),
                phone_number=fake.unique.phone_number(),
                birthday=fake.date_of_birth(),
                gender="M",
            )
            user2 = user_model.objects.create_user(
                email=fake.unique.email(),
                password="pw",
                name=fake.name(),
                nickname=fake.pystr(max_chars=10),
                phone_number=fake.unique.phone_number(),
                birthday=fake.date_of_birth(),
                gender="M",
            )
            # 24년도 5월 탈퇴한 유저 1명
            Withdrawals.objects.create(
                user=user2,
                reason=WithdrawalsReasonChoices.LACK_OF_INTEREST,
                reason_detail="test",
                due_date=date(2025, 9, 4),
            )

        with freeze_time("2025-09-12"):
            # 25년 9월 가입한 유저 1명
            user3 = user_model.objects.create_user(
                email=fake.unique.email(),
                password="pw",
                name=fake.name(),
                nickname=fake.pystr(max_chars=10),
                phone_number=fake.unique.phone_number(),
                birthday=fake.date_of_birth(),
                gender="M",
            )
            # 25년 9월 탈퇴한 유저 1명
            Withdrawals.objects.create(
                user=user3, reason=WithdrawalsReasonChoices.OTHER, reason_detail="test", due_date=date(2025, 9, 30)
            )

        cls.signup_url = reverse("admin_user:dashboard-signup-trends")
        cls.withdrawal_url = reverse("admin_user:dashboard-withdrawal-trends")
        cls.withdrawal_reason_url = reverse("admin_user:dashboard-withdrawal-reasons")

    def test_signup_trends_success(self) -> None:
        """대시보드 가입 추세 집계 API 데이터 반환 테스트"""
        self.client.force_authenticate(user=self.superuser)

        # 월 단위 조회 테스트
        response_monthly = self.client.get(self.signup_url, {"period": "monthly"})
        self.assertEqual(response_monthly.status_code, status.HTTP_200_OK)
        expected_monthly_data = {
            "2023-09": 1,
            "2025-08": 2,
            "2025-09": 1,
            "2025-10": 3,
        }
        self.assertEqual(response_monthly.data, expected_monthly_data)

        # 연 단위 조회 테스트
        response_yearly = self.client.get(self.signup_url, {"period": "yearly"})
        self.assertEqual(response_yearly.status_code, status.HTTP_200_OK)
        expected_yearly_data = {
            "2023": 1,
            "2025": 6,
        }
        self.assertEqual(response_yearly.data, expected_yearly_data)

    def test_withdrawal_trends_success(self) -> None:
        """대시보드 탈퇴 추세 집계 API 데이터 반환 테스트"""
        self.client.force_authenticate(user=self.superuser)

        response_monthly = self.client.get(self.withdrawal_url, {"period": "monthly"})
        self.assertEqual(response_monthly.status_code, status.HTTP_200_OK)
        excepted_data = {
            "2025-08": 1,
            "2025-09": 1,
        }
        self.assertEqual(response_monthly.data, excepted_data)

    def test_trends_permission_denied(self) -> None:
        """권한이 없는 유저 (일반유저)가 대시보드 API 접근시 403 에러 반환 테스트"""
        self.client.force_authenticate(user=self.general_user)

        sighup_response = self.client.get(self.signup_url)
        withdrawals_response = self.client.get(self.withdrawal_url)
        withdrawal_reason_response = self.client.get(self.withdrawal_reason_url, {"chart_type": "pie"})

        self.assertEqual(sighup_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(withdrawals_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(withdrawal_reason_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_withdrawal_reason_stats_success(self) -> None:
        """탈퇴 사유 통계 API가 올바르게 동작하는지 테스트 (원형/막대그래프)"""
        self.client.force_authenticate(user=self.superuser)

        with freeze_time("2025-10-01"):
            # 1. 원형 차트 데이터 테스트
            pie_response = self.client.get(self.withdrawal_reason_url, {"chart_type": "pie"})
            self.assertEqual(pie_response.status_code, status.HTTP_200_OK)
            # setUpTestData에서 생성한 데이터(OTHER: 1명, LACK_OF_INTEREST: 1명) 확인
            self.assertEqual(pie_response.data["OTHER"]["count"], 1)
            self.assertEqual(pie_response.data["LACK_OF_INTEREST"]["count"], 1)
            self.assertAlmostEqual(pie_response.data["OTHER"]["percentage"], 50.0)

            # 2. 막대 그래프 (전체 사유) 데이터 테스트
            bar_response_all = self.client.get(self.withdrawal_reason_url, {"chart_type": "bar"})
            self.assertEqual(bar_response_all.status_code, status.HTTP_200_OK)
            expected_all = {"2025-08": 1, "2025-09": 1}
            self.assertEqual(bar_response_all.data, expected_all)

            # 3. 막대 그래프 (특정 사유 필터링) 데이터 테스트
            bar_response_filtered = self.client.get(
                self.withdrawal_reason_url, {"chart_type": "bar", "reason": WithdrawalsReasonChoices.OTHER}
            )
            self.assertEqual(bar_response_filtered.status_code, status.HTTP_200_OK)
            expected_filtered = {"2025-09": 1}
            self.assertEqual(bar_response_filtered.data, expected_filtered)
