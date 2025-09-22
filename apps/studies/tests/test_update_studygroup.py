import logging
from datetime import datetime
from typing import Any, Dict, List

import boto3
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.test import TestCase, override_settings
from django.urls import reverse
from moto import mock_aws
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.tests.mixins.test_user_mixins import TestUserMixin
from apps.core.utils import create_temp_image
from apps.lectures.models import Lecture
from apps.lectures.models.crawled_lectures import DifficultyChoices, PlatformChoices
from apps.studies.models import StudyGroup
from apps.studies.serializers.study_group import StudyGroupCreateUpdateSerializer

logger = logging.getLogger(__name__)


@mock_aws
@override_settings(
    AWS_S3_BUCKET_NAME="test-bucket",
    AWS_S3_ACCESS_KEY_ID="fake",
    AWS_S3_SECRET_ACCESS_KEY="fake",
    AWS_S3_REGION="ap-northeast-2",
)
class UpdateStudyGroupTest(TestCase, TestUserMixin):
    """
    생성된 스터디 그룹을 수정하는 테스트.
    조건에 부합되는 데이터만 수정.
    """

    def setUp(self) -> None:
        self.user = self._create_test_user()
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

        # moto의 가짜 S3 클라이언트 생성
        self.s3 = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        )
        # 실제 코드와 동일한 버킷명으로 생성
        self.s3.create_bucket(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": settings.AWS_S3_REGION},
        )
        self.data = {
            "name": "스터디 그룹 수정 테스트",
            "introduction": "기본 데이터 생성",
            "max_headcount": 3,
            "start_at": datetime(2025, 10, 15),
            "end_at": datetime(2025, 10, 30),
            "lectures": [self.lecture.id],
            "profile_img": create_temp_image(),
        }
        self.target = StudyGroupCreateUpdateSerializer(data=self.data)
        self.assertTrue(self.target.is_valid(raise_exception=True))
        self.target.save(user=self.user)

    def test_update_fail(self) -> None:
        test_data: List[Dict[str, Any]] = [
            {"start_at": datetime(2025, 9, 1)},  # 과거 날짜
            {"end_at": datetime(2025, 10, 14)},  # 시작일 이전
            {"end_at": datetime(2025, 10, 17)},  # 최소기간
            {"max_headcount": 15},
        ]

        for case in test_data:
            set_up = get_object_or_404(StudyGroup, uuid=self.target.data["uuid"])
            serializer = StudyGroupCreateUpdateSerializer(instance=set_up, data=case, partial=True)
            self.assertFalse(serializer.is_valid())
            logger.debug(serializer.errors)

    def test_update_success(self) -> None:
        test_data: List[Dict[str, Any]] = [
            {"max_headcount": 5},
            {"profile_img": create_temp_image()},
            {"name": "이름 수정"},
        ]

        for case in test_data:
            set_up = get_object_or_404(StudyGroup, uuid=self.target.data["uuid"])
            serializer = StudyGroupCreateUpdateSerializer(instance=set_up, data=case, partial=True)
            self.assertTrue(serializer.is_valid(raise_exception=True))
            serializer.save(user=self.user)


@mock_aws
@override_settings(
    AWS_S3_BUCKET_NAME="test-bucket",
    AWS_S3_ACCESS_KEY_ID="fake",
    AWS_S3_SECRET_ACCESS_KEY="fake",
    AWS_S3_REGION="ap-northeast-2",
)
class UpdateStudyGroupAPITest(APITestCase, TestUserMixin):
    def setUp(self) -> None:
        self.user = self._create_test_user()
        self.client.force_authenticate(user=self.user)  # 유저 로그인
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

        # moto의 가짜 S3 클라이언트 생성
        self.s3 = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        )
        # 실제 코드와 동일한 버킷명으로 생성
        self.s3.create_bucket(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": settings.AWS_S3_REGION},
        )
        # 수정 테스트를 위한 데이터 생성
        self.data = {
            "name": "Python 개념 잡기",
            "introduction": "Python 언어 기초를 공부, 프로그래머스 문제 풀기.",
            "max_headcount": 5,
            "start_at": "2025-10-15T00:00:00Z",
            "end_at": "2025-10-30T00:00:00Z",
            "lectures": [self.lecture.id],
        }
        self.response = self.client.post(reverse("create_study_group"), data=self.data)
        self.study_group = StudyGroup.objects.get(
            uuid=self.response.data["uuid"]
        )  # 좀 더 좋은 방법이 있을거 같은데 모르겠음.
        self.url = reverse("update_study_group", kwargs={"group_uuid": self.study_group.uuid})

    def test_patch_fail(self) -> None:
        test_data = [  # 보완이 필요해보임.
            {"start_at": "2025-09-01T00:00:00Z"},  # 과거 날짜
            {"end_at": "2025-10-14T00:00:00Z"},  # 시작일 이전
            {"end_at": "2025-10-14T00:00:00Z"},  # 최소기간
            {"max_headcount": 15},
        ]
        for case in test_data:
            response = self.client.patch(self.url, data=case)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            logger.debug(response.data)

    def test_patch_success(self) -> None:
        test_data = [
            {"name": "인원 수정", "max_headcount": 5},
            {"name": "프로필 사진 추가", "profile_img": create_temp_image()},
            {"name": "스터디 일정 수정", "start_at": "2025-10-01T00:00:00Z", "end_at": "2025-10-31T00:00:00Z"},
        ]
        for case in test_data:
            response = self.client.patch(self.url, data=case)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_permission_fail(self) -> None:
        """
        리더 권한이 없는 경우 수정 실패 테스트
        :return:
        """
        self.new_user = self._create_test_user(email='kimshineday@test.com', nickname='김빛날', phone_number='01098765432') # 새로운 유저를 생성
        self.client.force_authenticate(user=self.new_user) # 새로운 유저로 로그인
        test_data = [
            {"name": "인원 수정", "max_headcount": 5},
            {"name": "프로필 사진 추가", "profile_img": create_temp_image()},
            {"name": "스터디 일정 수정", "start_at": "2025-10-01T00:00:00Z", "end_at": "2025-10-31T00:00:00Z"},
        ]
        for case in test_data:
            response = self.client.patch(self.url, data=case)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.study_group.refresh_from_db()
            self.assertEqual(self.study_group.name, "Python 개념 잡기")
            logger.debug(response.data)

