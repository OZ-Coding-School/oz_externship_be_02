from datetime import date, time, timedelta
from typing import ClassVar

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.studies.models import GroupMember, StudyGroup
from apps.study_group_schedules.models import GroupSchedule, ScheduleParticipant
from apps.study_group_schedules.services.schedule_services import (
    validate_user_can_edit_schedule,
)
from apps.users.models import User


class StudyGroupScheduleUpdateAPITestCase(APITestCase):
    """스터디 그룹 스케줄 수정 API 테스트"""

    leader_user: ClassVar[User]
    member_user: ClassVar[User]
    outsider_user: ClassVar[User]
    study_group: ClassVar[StudyGroup]
    other_study_group: ClassVar[StudyGroup]
    leader_member: ClassVar[GroupMember]
    normal_member: ClassVar[GroupMember]

    @classmethod
    def setUpTestData(cls) -> None:
        """테스트 데이터 설정"""
        # 테스트 사용자들 생성
        cls.leader_user = User.objects.create_user(
            email="leader@test.com",
            password="testpass123",
            name="리더김",
            nickname="리더",
            phone_number="010-1111-1111",
            gender="MALE",
            birthday=date(1990, 1, 1),
            is_active=True,
        )

        cls.member_user = User.objects.create_user(
            email="member@test.com",
            password="testpass123",
            name="멤버박",
            nickname="멤버",
            phone_number="010-2222-2222",
            gender="FEMALE",
            birthday=date(1992, 1, 1),
            is_active=True,
        )

        cls.outsider_user = User.objects.create_user(
            email="outsider@test.com",
            password="testpass123",
            name="외부인",
            nickname="외부인",
            phone_number="010-3333-3333",
            gender="MALE",
            birthday=date(1995, 1, 1),
            is_active=True,
        )

        # 스터디 그룹 생성
        cls.study_group = StudyGroup.objects.create(
            name="테스트 스터디 그룹",
            introduction="테스트용 스터디 그룹",
            max_headcount=5,
            start_at="2025-09-20T00:00:00Z",
            end_at="2025-12-20T23:59:59Z",
        )

        # 다른 스터디 그룹 (권한 테스트용)
        cls.other_study_group = StudyGroup.objects.create(
            name="다른 스터디 그룹",
            introduction="다른 테스트용 스터디 그룹",
            max_headcount=5,
            start_at="2025-09-20T00:00:00Z",
            end_at="2025-12-20T23:59:59Z",
        )

        # 그룹 멤버 추가
        cls.leader_member = GroupMember.objects.create(
            study_group=cls.study_group, user=cls.leader_user, is_leader=True
        )

        cls.normal_member = GroupMember.objects.create(
            study_group=cls.study_group, user=cls.member_user, is_leader=False
        )

    def setUp(self) -> None:
        """각 테스트마다 실행되는 설정"""
        # 기본 스케줄 생성
        tomorrow = date.today() + timedelta(days=1)
        self.schedule = GroupSchedule.objects.create(
            study_group=self.study_group,
            title="원본 스케줄",
            objective="원본 목표",
            session_date=tomorrow,
            start_time=time(14, 0),
            end_time=time(16, 0),
        )

        # 참여자 추가
        ScheduleParticipant.objects.create(schedule=self.schedule, member=self.leader_member)
        ScheduleParticipant.objects.create(schedule=self.schedule, member=self.normal_member)

    def tearDown(self) -> None:
        """각 테스트 후 정리"""
        GroupSchedule.objects.all().delete()
        ScheduleParticipant.objects.all().delete()

    def test_update_schedule_success_as_leader(self) -> None:
        """리더가 스케줄 수정 성공 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        update_data = {
            "title": "수정된 스케줄",
            "objective": "수정된 목표",
            "session_date": str(date.today() + timedelta(days=2)),
            "start_time": "15:00:00",
            "end_time": "17:00:00",
            "participant_ids": [self.leader_member.pk],
        }

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터 확인
        self.assertEqual(response.data["title"], "수정된 스케줄")
        self.assertEqual(response.data["objective"], "수정된 목표")
        self.assertEqual(response.data["start_time"], "15:00:00")
        self.assertEqual(response.data["end_time"], "17:00:00")

        # DB 확인
        updated_schedule = GroupSchedule.objects.get(id=self.schedule.id)
        self.assertEqual(updated_schedule.title, "수정된 스케줄")
        self.assertEqual(updated_schedule.objective, "수정된 목표")

        # 참여자 수 확인
        participant_count = ScheduleParticipant.objects.filter(schedule=updated_schedule).count()
        self.assertEqual(participant_count, 1)

    def test_update_schedule_forbidden_as_member(self) -> None:
        """일반 멤버의 스케줄 수정 시도 실패 테스트"""
        self.client.force_authenticate(user=self.member_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        update_data = {"title": "멤버가 수정한 스케줄", "start_time": "15:30:00"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_schedule_forbidden_as_outsider(self) -> None:
        """외부인의 수정 시도 실패 테스트"""
        self.client.force_authenticate(user=self.outsider_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        update_data = {"title": "외부인의 수정 시도"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_schedule_not_found(self) -> None:
        """존재하지 않는 스케줄 수정 시도 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": 99999},
        )

        update_data = {"title": "존재하지 않는 스케줄 수정"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_schedule_wrong_study_group(self) -> None:
        """다른 스터디 그룹의 스케줄 수정 시도 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.other_study_group.uuid, "schedule_id": self.schedule.id},
        )

        update_data = {"title": "다른 그룹에서 수정 시도"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_schedule_unauthenticated(self) -> None:
        """인증되지 않은 사용자의 수정 시도 테스트"""
        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        update_data = {"title": "인증 없는 수정 시도"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_schedule_invalid_time_range(self) -> None:
        """잘못된 시간 범위 수정 시도 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        # 종료 시간이 시작 시간보다 빠른 경우
        update_data = {"start_time": "16:00:00", "end_time": "14:00:00"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("종료 시간은 시작 시간보다 늦어야", str(response.data))

    def test_update_schedule_past_date(self) -> None:
        """과거 날짜로 수정 시도 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        # 어제 날짜로 수정 시도
        yesterday = date.today() - timedelta(days=1)
        update_data = {"session_date": str(yesterday)}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("과거 날짜로는", str(response.data))

    def test_update_schedule_invalid_participants(self) -> None:
        """잘못된 참여자 ID로 수정 시도 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        # 존재하지 않는 멤버 ID
        update_data = {"participant_ids": [99999]}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("스터디 그룹에 속하지 않은", str(response.data))

    def test_update_schedule_long_duration(self) -> None:
        """너무 긴 스터디 시간으로 수정 시도 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        # 9시간 스터디 (8시간 초과)
        update_data = {"start_time": "09:00:00", "end_time": "18:00:00"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("최대 8시간까지", str(response.data))

    def test_update_schedule_short_duration(self) -> None:
        """너무 짧은 스터디 시간으로 수정 시도 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        # 20분 스터디 (30분 미만)
        update_data = {"start_time": "14:00:00", "end_time": "14:20:00"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("최소 30분 이상", str(response.data))

    def test_update_schedule_empty_participants(self) -> None:
        """참여자를 모두 제거하는 수정 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        update_data: dict[str, list[int]] = {"participant_ids": []}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 참여자가 모두 제거되었는지 확인
        participant_count = ScheduleParticipant.objects.filter(schedule=self.schedule).count()
        self.assertEqual(participant_count, 0)

    def test_update_schedule_boundary_values(self) -> None:
        """경계값 테스트 (정확히 30분, 8시간)"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        # 정확히 30분 (허용되어야 함)
        update_data = {"start_time": "14:00:00", "end_time": "14:30:00"}

        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 정확히 8시간 (허용되어야 함)
        update_data = {"start_time": "09:00:00", "end_time": "17:00:00"}

        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_only_title(self) -> None:
        """제목만 수정하는 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        url = reverse(
            "schedule_update",
            kwargs={"study_group_uuid": self.study_group.uuid, "schedule_id": self.schedule.id},
        )

        update_data = {"title": "새로운 제목"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "새로운 제목")

        # 다른 필드는 변경되지 않았는지 확인
        self.assertEqual(response.data["objective"], "원본 목표")
        self.assertEqual(response.data["start_time"], "14:00:00")
        self.assertEqual(response.data["end_time"], "16:00:00")


class StudyGroupScheduleServiceTestCase(APITestCase):
    """스케줄 수정 서비스 함수 테스트"""

    user: ClassVar[User]
    study_group: ClassVar[StudyGroup]
    member: ClassVar[GroupMember]

    @classmethod
    def setUpTestData(cls) -> None:
        """테스트 데이터 설정"""
        cls.user = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            name="테스트유저",
            nickname="테스트사용자",
            phone_number="010-4444-4444",
            gender="MALE",
            birthday=date(1993, 1, 1),
            is_active=True,
        )

        cls.study_group = StudyGroup.objects.create(
            name="테스트 스터디 그룹",
            introduction="테스트용",
            max_headcount=5,
            start_at="2025-09-20T00:00:00Z",
            end_at="2025-12-20T23:59:59Z",
        )

        cls.member = GroupMember.objects.create(study_group=cls.study_group, user=cls.user, is_leader=True)

    def setUp(self) -> None:
        """각 테스트마다 실행되는 설정"""
        tomorrow = date.today() + timedelta(days=1)
        self.schedule = GroupSchedule.objects.create(
            study_group=self.study_group,
            title="테스트 스케줄",
            objective="테스트 목표",
            session_date=tomorrow,
            start_time=time(14, 0),
            end_time=time(16, 0),
        )

    def test_validate_user_can_edit_schedule_as_leader(self) -> None:
        """리더의 수정 권한 확인 테스트"""
        can_edit = validate_user_can_edit_schedule(self.user, self.schedule)
        self.assertTrue(can_edit)

    def test_validate_user_can_edit_schedule_as_member(self) -> None:
        """일반 멤버의 수정 권한 확인 테스트 - 리더만 가능"""
        # 비리더 사용자 생성
        member_user = User.objects.create_user(
            email="member@test.com",
            password="testpass123",
            name="멤버유저",
            nickname="멤버",
            phone_number="010-5555-5555",
            gender="FEMALE",
            birthday=date(1994, 1, 1),
            is_active=True,
        )

        GroupMember.objects.create(study_group=self.study_group, user=member_user, is_leader=False)

        can_edit = validate_user_can_edit_schedule(member_user, self.schedule)
        self.assertFalse(can_edit)

    def test_validate_user_can_edit_schedule_as_outsider(self) -> None:
        """외부인의 수정 권한 확인 테스트"""
        outsider = User.objects.create_user(
            email="outsider@test.com",
            password="testpass123",
            name="외부인",
            nickname="외부인",
            phone_number="010-6666-6666",
            gender="MALE",
            birthday=date(1996, 1, 1),
            is_active=True,
        )

        can_edit = validate_user_can_edit_schedule(outsider, self.schedule)
        self.assertFalse(can_edit)
