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


class WithdrawStudyGroupAPITest(APITestCase, TestUserMixin):
    """
    스터디 그룹원이 스터디 그룹에서 탈퇴하는 기능 테스트
    """

    def setUp(self) -> None:
        # 테스트를 위한 유저 생성
        self.leader = self._create_test_user()  # 스터디 그룹 리더
        self.member = self._create_test_user(
            email="kimshineday@test.com", nickname="김빛날", phone_number="01098765432"
        )  # 스터디 그룹원
        self.test_user = self._create_test_user(email="test@test.com", nickname="test", phone_number="01000000000")

        # 스터디 그룹 생성
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
            "name": "스터디 그룹 탈퇴 테스트",
            "introduction": "기본 데이터 생성",
            "max_headcount": 3,
            "start_at": datetime(2025, 10, 15),
            "end_at": datetime(2025, 10, 30),
            "lectures": [self.lecture.id],
        }
        self.group = StudyGroupCreateUpdateSerializer(data=self.data)
        self.assertTrue(self.group.is_valid(raise_exception=True))
        self.group.save(user=self.leader)
        self.study_group_member = GroupMember.objects.create(
            user=self.member, study_group=StudyGroup.objects.get(uuid=self.group.data["uuid"])
        )
        self.url = reverse("withdraw_study_group", kwargs={"group_uuid": self.group.data["uuid"]})

    def test_delete_fail_1(self) -> None:
        """
        스터디 그룹원이 아닌 경우 fail case
        """
        self.client.force_authenticate(user=self.test_user)  # 그룹원이 아닌 사람
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        logger.debug(response.data)

    def test_delete_fail_2(self) -> None:
        """
        스터디 그룹 리더인 경우 fail case
        """
        self.client.force_authenticate(user=self.leader)  # 스터디 그룹 리더
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        logger.debug(response.data)

    def test_delete_success(self) -> None:
        """
        success case!
        """
        self.client.force_authenticate(user=self.member)  # 스터디 그룹원
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
