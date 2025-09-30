from datetime import date, time, timedelta
from typing import ClassVar
from uuid import UUID

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.studies.models import GroupMember, StudyGroup
from apps.study_group_schedules.models import GroupSchedule, ScheduleParticipant
from apps.study_group_schedules.services.schedule_services import (
    validate_user_can_delete_schedule,
)
from apps.users.models import User


class StudyGroupScheduleDeleteAPITestCase(APITestCase):
    """스터디 그룹 스케줄 삭제 API 테스트"""

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
        tomorrow = date.today() + timedelta(days=1)
        self.schedule = GroupSchedule.objects.create(
            study_group=self.study_group,
            title="테스트 스케줄",
            objective="테스트 목표",
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

    def _get_delete_url(self, study_group_uuid: UUID, schedule_id: int) -> str:
        """삭제 URL 생성 헬퍼 메서드"""
        return reverse(
            "schedule_detail",
            kwargs={"study_group_uuid": study_group_uuid, "schedule_id": schedule_id},
        )

    def _assert_schedule_deleted(self, schedule_id: int) -> None:
        """스케줄이 삭제되었는지 확인하는 헬퍼 메서드"""
        self.assertFalse(GroupSchedule.objects.filter(id=schedule_id).exists())

    def _assert_schedule_exists(self, schedule_id: int) -> None:
        """스케줄이 존재하는지 확인하는 헬퍼 메서드"""
        self.assertTrue(GroupSchedule.objects.filter(id=schedule_id).exists())

    def _assert_participants_deleted(self, schedule_id: int) -> None:
        """참여자 정보가 삭제되었는지 확인하는 헬퍼 메서드"""
        self.assertFalse(ScheduleParticipant.objects.filter(schedule_id=schedule_id).exists())

    def test_delete_schedule_success_as_leader(self) -> None:
        """리더가 스케줄 삭제 성공 테스트"""
        self.client.force_authenticate(user=self.leader_user)
        url = self._get_delete_url(self.study_group.uuid, self.schedule.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self._assert_schedule_deleted(self.schedule.id)
        self._assert_participants_deleted(self.schedule.id)

    def test_delete_schedule_success_as_member(self) -> None:
        """일반 멤버의 스케줄 삭제 성공 테스트"""
        self.client.force_authenticate(user=self.member_user)
        url = self._get_delete_url(self.study_group.uuid, self.schedule.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self._assert_schedule_deleted(self.schedule.id)

    def test_delete_schedule_forbidden_as_outsider(self) -> None:
        """외부인의 삭제 시도 실패 테스트"""
        self.client.force_authenticate(user=self.outsider_user)
        url = self._get_delete_url(self.study_group.uuid, self.schedule.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self._assert_schedule_exists(self.schedule.id)

    def test_delete_schedule_not_found(self) -> None:
        """존재하지 않는 스케줄 삭제 시도 테스트"""
        self.client.force_authenticate(user=self.leader_user)
        url = self._get_delete_url(self.study_group.uuid, 99999)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_schedule_wrong_study_group(self) -> None:
        """다른 스터디 그룹의 스케줄 삭제 시도 테스트"""
        self.client.force_authenticate(user=self.leader_user)
        url = self._get_delete_url(self.other_study_group.uuid, self.schedule.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self._assert_schedule_exists(self.schedule.id)

    def test_delete_schedule_unauthenticated(self) -> None:
        """인증되지 않은 사용자의 삭제 시도 테스트"""
        url = self._get_delete_url(self.study_group.uuid, self.schedule.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self._assert_schedule_exists(self.schedule.id)

    def test_delete_multiple_schedules(self) -> None:
        """여러 스케줄 삭제 테스트"""
        self.client.force_authenticate(user=self.leader_user)

        # 추가 스케줄 생성
        schedule2 = GroupSchedule.objects.create(
            study_group=self.study_group,
            title="두 번째 스케줄",
            objective="두 번째 목표",
            session_date=date.today() + timedelta(days=2),
            start_time=time(15, 0),
            end_time=time(17, 0),
        )

        schedule3 = GroupSchedule.objects.create(
            study_group=self.study_group,
            title="세 번째 스케줄",
            objective="세 번째 목표",
            session_date=date.today() + timedelta(days=3),
            start_time=time(16, 0),
            end_time=time(18, 0),
        )

        # 첫 번째 스케줄 삭제
        url1 = self._get_delete_url(self.study_group.uuid, self.schedule.id)
        response1 = self.client.delete(url1)
        self.assertEqual(response1.status_code, status.HTTP_204_NO_CONTENT)

        # 두 번째 스케줄 삭제
        url2 = self._get_delete_url(self.study_group.uuid, schedule2.id)
        response2 = self.client.delete(url2)
        self.assertEqual(response2.status_code, status.HTTP_204_NO_CONTENT)

        # 검증
        self._assert_schedule_deleted(self.schedule.id)
        self._assert_schedule_deleted(schedule2.id)
        self._assert_schedule_exists(schedule3.id)

    def test_delete_schedule_with_many_participants(self) -> None:
        """많은 참여자가 있는 스케줄 삭제 테스트"""
        # 추가 멤버 생성
        for i in range(5):
            user = User.objects.create_user(
                email=f"user{i}@test.com",
                password="testpass123",
                name=f"사용자{i}",
                nickname=f"유저{i}",
                phone_number=f"010-4444-444{i}",
                gender="MALE",
                birthday=date(1995, 1, 1),
                is_active=True,
            )
            member = GroupMember.objects.create(study_group=self.study_group, user=user, is_leader=False)
            ScheduleParticipant.objects.create(schedule=self.schedule, member=member)

        # 참여자 수 확인
        participant_count = ScheduleParticipant.objects.filter(schedule=self.schedule).count()
        self.assertEqual(participant_count, 7)  # 기존 2명 + 추가 5명

        self.client.force_authenticate(user=self.leader_user)
        url = self._get_delete_url(self.study_group.uuid, self.schedule.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self._assert_participants_deleted(self.schedule.id)


class StudyGroupScheduleDeleteServiceTestCase(APITestCase):
    """스케줄 삭제 서비스 함수 테스트"""

    user: ClassVar[User]
    study_group: ClassVar[StudyGroup]
    member: ClassVar[GroupMember]
    schedule: GroupSchedule

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

    def _create_user(self, email: str, nickname: str, phone_number: str, is_leader: bool = False) -> User:
        """테스트 사용자 생성 헬퍼 메서드"""
        user = User.objects.create_user(
            email=email,
            password="testpass123",
            name=nickname,
            nickname=nickname,
            phone_number=phone_number,
            gender="MALE",
            birthday=date(1994, 1, 1),
            is_active=True,
        )
        GroupMember.objects.create(study_group=self.study_group, user=user, is_leader=is_leader)
        return user

    def test_validate_user_can_delete_schedule_as_leader(self) -> None:
        """리더의 삭제 권한 확인 테스트"""
        can_delete = validate_user_can_delete_schedule(self.user, self.schedule)
        self.assertTrue(can_delete)

    def test_validate_user_can_delete_schedule_as_member(self) -> None:
        """일반 멤버의 삭제 권한 확인 테스트"""
        member_user = self._create_user("member@test.com", "멤버", "010-5555-5555", is_leader=False)

        can_delete = validate_user_can_delete_schedule(member_user, self.schedule)
        self.assertTrue(can_delete)

    def test_validate_user_can_delete_schedule_as_outsider(self) -> None:
        """외부인의 삭제 권한 확인 테스트"""
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

        can_delete = validate_user_can_delete_schedule(outsider, self.schedule)
        self.assertFalse(can_delete)
