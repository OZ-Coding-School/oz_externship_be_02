import logging
from datetime import datetime
from typing import Any, Dict, List, cast

import boto3
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from moto import mock_aws
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.tests.mixins.test_user_mixins import TestUserMixin
from apps.core.utils import create_temp_image
from apps.lectures.models import Lecture
from apps.lectures.models.crawled_lectures import DifficultyChoices, PlatformChoices
from apps.studies.models import GroupMember, StudyGroup, StudyLecture
from apps.studies.serializers.study_group import StudyGroupCreateUpdateSerializer

logger = logging.getLogger(__name__)


class CreateStudyGroupTestFalse(TestCase, TestUserMixin):
    """
    * test 실패
        - 스터디 그룹 생성 시, 잘못된 데이터 입력. 누락된 값이 있을 경우.
        - 스터디 그룹 생성 시, 유저 데이터 없을 경우.
        - 검증 시 False 출력
    """

    def setUp(self) -> None:
        self.user = self._create_test_user()

    def test_create_fail(self) -> None:
        fail_data: List[Dict[str, Any]] = [
            {"study_group": {}},  # 깡통 데이터
            {
                "study_group": {  # 스터디 기간 조건 X
                    "name": "테스트",
                    "introduction": "스터디그룹 생성 테스트 진행 중",
                    "max_headcount": 4,
                    "profile_img": create_temp_image(),
                    "start_at": datetime(2025, 9, 28),
                    "end_at": datetime(2025, 9, 30),
                }
            },
        ]

        for case in fail_data:
            serializer = StudyGroupCreateUpdateSerializer(data=case["study_group"])
            self.assertFalse(serializer.is_valid())


@override_settings(
    AWS_S3_BUCKET_NAME="test-bucket",
    AWS_S3_ACCESS_KEY_ID="fake",  # 아무 값이나 가능
    AWS_S3_SECRET_ACCESS_KEY="fake",
    AWS_S3_REGION="ap-northeast-2",
)
@mock_aws
class CreateStudyGroupTestSuccess(TestCase, TestUserMixin):
    """
    데이터 입력.
    test_create_group2 : 이미지 url 생략
    test_create_group3 : 이미지 url 포함
    """

    def setUp(self) -> None:
        """
        가상 user data 생성
        """
        # 스터디 그룹 생성 시, 생성자를 그룹 리더로 저장하기 위해 시리얼라이저에서 그룹 데이터 저장 후에 멤버 저장 로직까지 구현완료
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
        self.user = self._create_test_user()
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

    def test_create_success(self) -> None:  # 테스트 성공, 이미지 url 생략
        success_data = [
            {
                "name": "테스트 성공기원 1",
                "introduction": "이미지 필수 아니여서 제외.",
                "max_headcount": 3,
                "profile_img": create_temp_image(),
                "start_at": datetime(2025, 10, 15),
                "end_at": datetime(2025, 10, 30),
                "lectures": [self.lecture.id],
            },
            {
                "name": "테스트 성공기원 2",
                "introduction": "스터디 그룹 프로필 이미지 추가.",
                "max_headcount": 3,
                "profile_img": create_temp_image(),
                "start_at": datetime(2025, 10, 15),
                "end_at": datetime(2025, 10, 30),
                "lectures": [self.lecture.id],
            },
        ]

        for data in success_data:
            serializer = StudyGroupCreateUpdateSerializer(
                data=data,
            )
            self.assertTrue(serializer.is_valid(raise_exception=True))

            # 데이터 객체 생성
            serializer.save(user=self.user)

    def tearDown(self) -> None:
        """
        test db에 저장된 데이터 확인
        :return: data
        """
        all_groups = StudyGroup.objects.all().values()
        all_members = GroupMember.objects.all().values()
        logger.debug(f"Groups: {all_groups}")
        logger.debug(f"Members: {all_members}")


class CreateStudyGroupAPITestFail(APITestCase, TestUserMixin):
    """
    post 요청을 통해 스터디 그룹 생성하지 못하는 테스트
    """

    def setUp(self) -> None:
        """
        가상 user data 생성
        """
        self.url = reverse("create_study_group")  # 라우터 설정
        self.user = self._create_test_user()
        self.client.force_authenticate(user=self.user)  # 유저 로그인

    def test_post_fail(self) -> None:
        """
        스터디 그룹 작성 API, post 요청 테스트
        결과 값 400
        :return:
        """
        fail_data = [
            {
                "name": "API 실패 테스트 1",
                "introduction": "인원 초과",
                "max_headcount": 11,
                "start_at": "2025-10-15T00:00:00Z",
                "end_at": "2025-10-30T00:00:00Z",
            },
            {
                "name": "API 실패 테스트 2",
                "introduction": "일정 설정 오류 - 시작날이 오늘 / 오늘 이후",
                "max_headcount": 6,
                "start_at": "2025-09-01T00:00:00Z",
                "end_at": "2025-09-30T00:00:00Z",
            },
            {
                "name": "API 실패 테스트 3",
                "introduction": "일정 설정 오류 - 끝나는 날짜가 시작날보다 이전",
                "max_headcount": 6,
                "start_at": "2025-10-30T00:00:00Z",
                "end_at": "2025-10-15T00:00:00Z",
            },
            {
                "name": "API 실패 테스트 4",
                "introduction": "일정 설정 오류 - 스터디는 최소 5일 진행",
                "max_headcount": 6,
                "start_at": "2025-10-01T00:00:00Z",
                "end_at": "2025-10-03T00:00:00Z",
            },
        ]

        for data in fail_data:
            response = self.client.post(self.url, data=data)
            self.assertEqual(response.status_code, 400)


@mock_aws
@override_settings(
    AWS_S3_BUCKET_NAME="test-bucket",
    AWS_S3_ACCESS_KEY_ID="fake",
    AWS_S3_SECRET_ACCESS_KEY="fake",
    AWS_S3_REGION="ap-northeast-2",
)
class CreateStudyGroupAPITestSuccess(APITestCase, TestUserMixin):
    """
    post 요청을 통해 스터디 그룹을 생성하는 테스트
    """

    def setUp(self) -> None:
        self.url = reverse("create_study_group")  # 라우터 설정
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

    def test_post_success(self) -> None:
        """
        스터디 그룹 작성 API, post 요청 테스트
        결과 값 201
        :return:
        """
        success_data = {
            "name": "Python 개념 잡기",
            "introduction": "Python 언어 기초를 공부, 프로그래머스 문제 풀기.",
            "max_headcount": 5,
            "profile_img": create_temp_image(),  # 이미지 값 추가
            "start_at": "2025-10-15T00:00:00Z",
            "end_at": "2025-10-30T00:00:00Z",
            "lectures": [self.lecture.id],
        }

        response = self.client.post(self.url, data=success_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Python 개념 잡기")
        self.assertEqual(StudyGroup.objects.count(), 1)
        created_study_group = cast(StudyGroup, StudyGroup.objects.filter(uuid=response.data["uuid"]).first())
        self.assertIsNotNone(created_study_group.profile_img_url)
        self.assertEqual(created_study_group.lectures.count(), 1)
        created_member = cast(
            GroupMember, GroupMember.objects.filter(user=self.user, study_group_id=created_study_group.id).first()
        )
        self.assertTrue(created_member.is_leader)
