from datetime import date, timedelta
from typing import ClassVar

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.studies.models import StudyGroup
from apps.study_group_schedules.models import GroupSchedule
from apps.users.models.user import User


class StudyGroupScheduleListTest(APITestCase):
    test_user: ClassVar[User]
    test_other_user: ClassVar[User]
    test_study_group: ClassVar[StudyGroup]
    test_other_study_group: ClassVar[StudyGroup]

    @classmethod
    def setUpTestData(cls) -> None:
        """클래스 레벨에서 한 번만 실행되는 공통 데이터 설정"""
        # 테스트 사용자들 생성
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

        cls.test_other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            name="다른유저",
            nickname="other",
            phone_number="010-9876-5432",
            gender="FEMALE",
            birthday=date(2000, 1, 1),
            is_active=True,
        )

        # 스터디 그룹 생성
        cls.test_study_group = StudyGroup.objects.create(
            name="테스트 스터디 그룹",
            introduction="테스트용 스터디 그룹",
            max_headcount=5,
            start_at="2025-09-20T00:00:00Z",
            end_at="2025-10-21T23:59:59Z",
        )

        cls.test_other_study_group = StudyGroup.objects.create(
            name="다른 스터디 그룹",
            introduction="다른 테스트용 스터디 그룹",
            max_headcount=5,
            start_at="2025-09-20T00:00:00Z",
            end_at="2025-10-21T23:59:59Z",
        )

        # 사용자를 스터디 그룹에 추가
        cls.test_study_group.members.add(cls.test_user)
        cls.test_other_study_group.members.add(cls.test_other_user)

    def setUp(self) -> None:
        """각 테스트마다 실행되는 설정"""
        # 인증 설정
        self.client.force_authenticate(user=self.test_user)

        # 테스트 스케줄 데이터 생성
        today = date.today()
        self.schedules = [
            GroupSchedule.objects.create(
                study_group=self.test_study_group,
                title="1주차 스터디",
                objective="Python 기초",
                session_date=today + timedelta(days=1),
                start_time="14:00:00",
                end_time="16:00:00",
            ),
            GroupSchedule.objects.create(
                study_group=self.test_study_group,
                title="2주차 스터디",
                objective="Django 기초",
                session_date=today + timedelta(days=8),
                start_time="14:00:00",
                end_time="16:00:00",
            ),
            GroupSchedule.objects.create(
                study_group=self.test_study_group,
                title="3주차 스터디",
                objective="DRF 기초",
                session_date=today + timedelta(days=15),
                start_time="14:00:00",
                end_time="16:00:00",
            ),
        ]

    def tearDown(self) -> None:
        """각 테스트 후 생성된 스케줄 정리"""
        GroupSchedule.objects.all().delete()

    def test_list_schedules_success(self) -> None:
        """스케줄 목록 조회 성공 테스트"""
        url = reverse("schedule_list", kwargs={"study_group_id": self.test_study_group.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

        # 최신순 정렬 확인 (기본값)
        results = response.data["results"]
        self.assertEqual(results[0]["title"], "3주차 스터디")
        self.assertEqual(results[1]["title"], "2주차 스터디")
        self.assertEqual(results[2]["title"], "1주차 스터디")

    def test_list_schedules_with_date_filter(self) -> None:
        """날짜 필터링 테스트"""
        today = date.today()
        url = reverse("schedule_list", kwargs={"study_group_id": self.test_study_group.uuid})

        # 특정 기간 필터링
        response = self.client.get(
            url,
            {
                "start_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
                "end_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "2주차 스터디")

    def test_list_schedules_access_denied(self) -> None:
        """접근 권한 없는 스터디 그룹 조회 실패 테스트"""
        url = reverse("schedule_list", kwargs={"study_group_id": self.test_other_study_group.uuid})
        response = self.client.get(url)

        # 권한이 없는 경우 빈 결과 반환
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_list_schedules_unauthenticated(self) -> None:
        """미인증 사용자 접근 테스트"""
        self.client.logout()
        url = reverse("schedule_list", kwargs={"study_group_id": self.test_study_group.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
