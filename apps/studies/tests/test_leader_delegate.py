import logging
from datetime import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.tests.mixins.test_user_mixins import TestUserMixin
from apps.lectures.models import Lecture
from apps.lectures.models.crawled_lectures import DifficultyChoices, PlatformChoices
from apps.studies.models import GroupMember, StudyGroup
from apps.studies.serializers.study_group import StudyGroupCreateUpdateSerializer

logger = logging.getLogger(__name__)


class LeaderDelegateTests(APITestCase, TestUserMixin):
    def setUp(self) -> None:
        """
        테스트를 위해 유저 생성 및 스터디 그룹 생성
        """
        self.leader = self._create_test_user()
        self.newleader = self._create_test_user(
            email="kimshineday@test.com", nickname="김빛날", phone_number="01098765432"
        )
        self.test_user = self._create_test_user(
            email="testuser@test.com", nickname="테스트", phone_number="01000001111"
        )
        self.lecture = Lecture.objects.create(
            title="test lecture",
            instructor="김인직",
            average_rating=4.23,
            duration=20,
            difficulty=DifficultyChoices.NORMAL,
            description="testtest",
            platform=PlatformChoices.INFLEARN,
            original_price=40000,
            discount_price=32000,
            url_link="https://ozcoding.site/lectures/1",
        )
        self.data = {
            "name": "스터디 그룹 리더 위임 테스트",
            "introduction": "기본 데이터 생성",
            "max_headcount": 3,
            "start_at": datetime(2025, 10, 15),
            "end_at": datetime(2025, 10, 30),
            "lectures": [self.lecture.id],
        }
        self.serializer = StudyGroupCreateUpdateSerializer(data=self.data)
        self.assertTrue(self.serializer.is_valid(raise_exception=True))
        self.study_group = self.serializer.save(user=self.leader)
        self.study_group_member = GroupMember.objects.create(
            user=self.newleader, study_group=StudyGroup.objects.get(uuid=self.study_group.uuid)
        )
        # API
        self.url = reverse("leader_delegate", kwargs={"group_uuid": self.study_group.uuid})

    def test_delegate_fail_1(self) -> None:
        """
        리더 권한이 없는데 요청했을 경우.
        """
        self.client.force_authenticate(user=self.newleader)  # 스터디 그룹원

        self.new_leader_data = {"new_leader_id": self.newleader.uuid}
        response = self.client.post(self.url, data=self.new_leader_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # 권한 X
        new_leader = GroupMember.objects.get(user=self.newleader)
        previous_leader = GroupMember.objects.get(user=self.leader)
        # 데이터 변환 값 X
        self.assertEqual(new_leader.is_leader, False)
        self.assertEqual(previous_leader.is_leader, True)
        logger.debug(response.data)

    def test_delegate_fail_2(self) -> None:
        """
        스터디 그룹원이 아닌 사람에게 리더 위임을 할 경우.
        """
        self.client.force_authenticate(user=self.leader)  # 스터디 그룹 리더
        self.new_leader_data = {"new_leader_id": self.test_user.uuid}  # 그룹원이 아닌 유저를 지정
        response = self.client.post(self.url, data=self.new_leader_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        previous_leader = GroupMember.objects.get(user=self.leader)
        self.assertEqual(previous_leader.is_leader, True)  # 기존 리더 권한 유지
        logger.debug(response.data)

    def test_delegate_success(self) -> None:
        """
        성공 케이스
        """
        self.client.force_authenticate(user=self.leader)  # 스터디 그룹 리더

        self.new_leader_data = {"new_leader_id": self.newleader.uuid}
        response = self.client.post(self.url, data=self.new_leader_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_leader = GroupMember.objects.get(study_group=self.study_group, user=self.newleader)
        previous_leader = GroupMember.objects.get(study_group=self.study_group, user=self.leader)
        # 데이터 변경
        self.assertEqual(new_leader.is_leader, True)
        self.assertEqual(previous_leader.is_leader, False)
