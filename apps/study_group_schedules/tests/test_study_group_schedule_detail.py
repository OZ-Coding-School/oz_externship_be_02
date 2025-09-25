from datetime import date, timedelta
from typing import ClassVar
from uuid import uuid4

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.studies.models import StudyGroup
from apps.study_group_schedules.models import GroupSchedule
from apps.users.models.user import User


class StudyGroupScheduleDetailTestCase(APITestCase):
    """스터디 그룹 스케줄 상세조회 테스트 케이스"""

    # 클래스 변수 타입 주석
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

        # 다른 스터디 그룹의 스케줄 (접근 권한 없음)
        self.other_schedule = GroupSchedule.objects.create(
            study_group=self.test_other_study_group,
            title="다른 그룹 스케줄",
            objective="접근 권한 테스트",
            session_date=date.today() + timedelta(days=7),
            start_time="14:00:00",
            end_time="16:00:00",
        )

    def tearDown(self) -> None:
        """각 테스트 후 정리"""
        GroupSchedule.objects.all().delete()

    def test_get_schedule_detail_success(self) -> None:
        """스케줄 상세조회 성공 테스트"""
        url = reverse(
            "schedule_detail",
            kwargs={"study_group_uuid": self.test_study_group.uuid, "schedule_id": self.schedules[0].id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터 검증
        data = response.data
        self.assertEqual(data["id"], self.schedules[0].id)
        self.assertEqual(data["title"], self.schedules[0].title)
        self.assertEqual(data["objective"], self.schedules[0].objective)
        self.assertEqual(data["study_group"]["study_group_uuid"], str(self.test_study_group.uuid))
        self.assertEqual(data["study_group"]["study_group_name"], self.test_study_group.name)

    def test_get_schedule_detail_not_found(self) -> None:
        """존재하지 않는 스케줄 조회 테스트"""
        url = reverse(
            "schedule_detail",
            kwargs={"study_group_uuid": self.test_study_group.uuid, "schedule_id": 99999},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "해당 스케줄을 찾을 수 없습니다.")

    def test_get_schedule_detail_access_denied(self) -> None:
        """접근 권한 없는 스케줄 조회 테스트"""
        url = reverse(
            "schedule_detail",
            kwargs={"study_group_uuid": self.test_other_study_group.uuid, "schedule_id": self.other_schedule.id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "해당 스케줄에 대한 접근 권한이 없습니다.")

    def test_get_schedule_detail_wrong_study_group(self) -> None:
        """잘못된 스터디 그룹 UUID로 조회 테스트"""
        wrong_uuid = uuid4()
        url = reverse(
            "schedule_detail",
            kwargs={"study_group_uuid": wrong_uuid, "schedule_id": self.schedules[0].id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "해당 스케줄을 찾을 수 없습니다.")

    def test_get_schedule_detail_unauthenticated(self) -> None:
        """미인증 사용자 접근 테스트"""
        self.client.logout()
        url = reverse(
            "schedule_detail",
            kwargs={"study_group_uuid": self.test_study_group.uuid, "schedule_id": self.schedules[0].id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("authentication credentials", str(response.content))
