from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.studies.models import StudyGroup
from apps.study_group_schedules.models import GroupSchedule
from apps.users.models.user import User


class StudyGroupScheduleCreateTest(APITestCase):
    def setUp(self) -> None:
        """테스트용 유저와 스터디 그룹 생성"""
        self.user = User.objects.create_user(
            email="kimOz@example.com",
            password="password123",
            name="김오즈",
            nickname="wicked",
            phone_number="010-1234-5678",
            gender="MALE",
            birthday=date(1999, 12, 31),
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

        self.study_group = StudyGroup.objects.create(
            name="스터디 그룹",
            introduction="테스트용 스터디 그룹",
            max_headcount=5,
            start_at="2025-09-08T00:00:00Z",
            end_at="2025-09-19T23:59:59Z",
        )

        self.valid_data = {
            "study_group": self.study_group.id,
            "title": "1주차 스터디",
            "objective": "Django REST Framework 기초 학습",
            "session_date": "2025-09-08",
            "start_time": "14:00:00",
            "end_time": "18:00:00",
        }

    def test_create_schedule_success(self) -> None:
        """스케줄 생성 성공 테스트"""
        url = reverse("create_schedule")
        response = self.client.post(url, self.valid_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GroupSchedule.objects.count(), 1)

        schedule = GroupSchedule.objects.first()
        assert schedule is not None
        self.assertEqual(schedule.title, "1주차 스터디")
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
