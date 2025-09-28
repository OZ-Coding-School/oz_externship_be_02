from datetime import date, timedelta
from typing import Any, ClassVar

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.studies.models import StudyGroup
from apps.study_group_schedules.models import GroupSchedule
from apps.users.models.user import User


class StudyGroupScheduleCreateTest(APITestCase):
    test_user: ClassVar[User]
    test_study_group: ClassVar[StudyGroup]

    @classmethod
    def setUpTestData(cls) -> None:
        """클래스 레벨에서 한 번만 실행되는 공통 데이터 설정"""
        # 공통 사용자 생성
        cls.test_user = User.objects.create_user(
            email="kimOz@example.com",
            password="password123",
            name="김오즈",
            nickname="wicked",
            phone_number="010-1234-5678",
            gender="MALE",
            birthday=date(1999, 12, 31),
            is_active=True,
        )

        # 공통 스터디 그룹 생성
        cls.test_study_group = StudyGroup.objects.create(
            name="스터디 그룹",
            introduction="테스트용 스터디 그룹",
            max_headcount=5,
            start_at="2025-09-20T00:00:00Z",
            end_at="2025-10-21T23:59:59Z",
        )

    def setUp(self) -> None:
        """각 테스트마다 실행되는 설정"""
        # 인증 설정
        self.client.force_authenticate(user=self.test_user)

        # 기존 코드 호환성을 위한 변수 설정
        self.user = self.test_user
        self.study_group = self.test_study_group

        # 각 테스트에서 사용할 데이터 (수정 가능)
        tomorrow = date.today() + timedelta(days=1)  # 내일 날짜로 설정

        self.valid_data = {
            "study_group": self.test_study_group.uuid,
            "title": "1주차 스터디",
            "objective": "Django REST Framework 기초 학습",
            "session_date": tomorrow.strftime("%Y-%m-%d"),  # 동적 날짜 설정
            "start_time": "14:00:00",
            "end_time": "18:00:00",
        }

    @classmethod
    def tearDownClass(cls) -> None:
        """클래스의 모든 테스트가 끝난 후 리소스 정리"""
        if hasattr(cls, "test_study_group"):
            cls.test_study_group.delete()

        if hasattr(cls, "test_user"):
            cls.test_user.delete()

        super().tearDownClass()

    def tearDown(self) -> None:
        """각 테스트 후 생성된 스케줄 정리"""
        GroupSchedule.objects.all().delete()

    def test_create_schedule_success(self) -> None:
        """스케줄 생성 성공 테스트"""
        url = reverse("create_schedule")
        response = self.client.post(url, self.valid_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GroupSchedule.objects.count(), 1)

        schedule = GroupSchedule.objects.first()
        assert schedule is not None
        self.assertEqual(schedule.title, self.valid_data["title"])
        self.assertEqual(schedule.study_group, self.study_group)

        # Response 데이터 검증
        self.assertEqual(response.data["title"], "1주차 스터디")
        self.assertEqual(response.data["study_group_name"], "스터디 그룹")

    def test_create_schedule_invalid_time(self) -> None:
        """잘못된 시간 설정 테스트 (시작 시간 >= 종료 시간)"""
        invalid_data = self.valid_data.copy()
        invalid_data["start_time"] = "18:00:00"
        invalid_data["end_time"] = "14:00:00"

        url = reverse("create_schedule")
        response = self.client.post(url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("시작 시간은 종료 시간보다 이전이어야 합니다.", str(response.data))
        self.assertEqual(GroupSchedule.objects.count(), 0)

    def test_create_schedule_same_time(self) -> None:
        """동일한 시작/종료 시간 테스트"""
        invalid_data = self.valid_data.copy()
        invalid_data["start_time"] = "14:00:00"
        invalid_data["end_time"] = "14:00:00"

        url = reverse("create_schedule")
        response = self.client.post(url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GroupSchedule.objects.count(), 0)

    def test_create_schedule_insufficient_duration_20_minutes(self) -> None:
        """30분 미만 시간 간격 테스트 (29분)"""
        invalid_data = self.valid_data.copy()
        invalid_data["start_time"] = "14:00:00"
        invalid_data["end_time"] = "14:29:00"  # 29분 간격

        url = reverse("create_schedule")
        response = self.client.post(url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("스터디 시간은 최소 30분 이상이어야 합니다.", str(response.data))
        self.assertEqual(GroupSchedule.objects.count(), 0)

    def test_create_schedule_minimum_valid_duration(self) -> None:
        """최소 유효 시간(30분) 테스트 (성공해야 함)"""
        valid_data = self.valid_data.copy()
        valid_data["start_time"] = "14:00:00"
        valid_data["end_time"] = "14:30:00"  # 정확히 30분

        url = reverse("create_schedule")
        response = self.client.post(url, valid_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GroupSchedule.objects.count(), 1)

        schedule = GroupSchedule.objects.first()
        assert schedule is not None
        self.assertEqual(str(schedule.start_time), "14:00:00")
        self.assertEqual(str(schedule.end_time), "14:30:00")

    def test_create_schedule_missing_required_fields(self) -> None:
        """필수 필드 누락 테스트"""
        test_cases = [
            {"study_group": ""},
            {"title": ""},
            {"objective": ""},
            {"session_date": ""},
            {"start_time": ""},
            {"end_time": ""},
        ]

        for invalid_field in test_cases:
            with self.subTest(invalid_field=invalid_field):
                data = self.valid_data.copy()
                data.update(invalid_field)

                url = reverse("create_schedule")
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_schedule_invalid_study_group(self) -> None:
        """존재하지 않는 스터디 그룹 ID 테스트"""
        invalid_data = self.valid_data.copy()
        invalid_data["study_group"] = "99999999-9999-9999-9999-999999999999"

        url = reverse("create_schedule")
        response = self.client.post(url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GroupSchedule.objects.count(), 0)

    def test_create_schedule_invalid_date_format(self) -> None:
        """잘못된 날짜 형식 테스트"""
        invalid_data = self.valid_data.copy()
        invalid_data["session_date"] = "2025/09/08"

        url = reverse("create_schedule")
        response = self.client.post(url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_schedule_invalid_time_format(self) -> None:
        """잘못된 시간 형식 테스트"""
        invalid_data = self.valid_data.copy()
        invalid_data["start_time"] = "2:00 PM"

        url = reverse("create_schedule")
        response = self.client.post(url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_schedule_past_date(self) -> None:
        """과거 날짜 스케줄 생성 테스트 (실패해야 함)"""

        invalid_data = self.valid_data.copy()
        past_date = date.today() - timedelta(days=1)  # 어제
        invalid_data["session_date"] = past_date.strftime("%Y-%m-%d")

        url = reverse("create_schedule")
        response = self.client.post(url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("스케줄 날짜는 오늘 이후로만 설정 가능합니다.", str(response.data))
        self.assertEqual(GroupSchedule.objects.count(), 0)

    def test_create_schedule_today_date(self) -> None:
        """오늘 날짜 스케줄 생성 테스트 (성공해야 함)"""

        valid_data = self.valid_data.copy()
        today = date.today()
        valid_data["session_date"] = today.strftime("%Y-%m-%d")

        url = reverse("create_schedule")
        response = self.client.post(url, valid_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GroupSchedule.objects.count(), 1)

    def test_create_schedule_future_date(self) -> None:
        """미래 날짜 스케줄 생성 테스트 (성공해야 함)"""

        valid_data = self.valid_data.copy()
        future_date = date.today() + timedelta(days=7)  # 일주일 후
        valid_data["session_date"] = future_date.strftime("%Y-%m-%d")

        url = reverse("create_schedule")
        response = self.client.post(url, valid_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GroupSchedule.objects.count(), 1)
