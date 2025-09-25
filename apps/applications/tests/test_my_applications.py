from datetime import datetime
from io import BytesIO

import boto3
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from moto import mock_aws
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models import Application
from apps.recruitments.models import Recruitment, RecruitmentImage
from apps.studies.models import StudyGroup
from apps.users.models import User


def get_test_image() -> SimpleUploadedFile:
    image_io = BytesIO()
    image = Image.new("RGB", (1, 1), color=(255, 255, 255))
    image.save(image_io, format="JPEG")
    image_io.seek(0)
    return SimpleUploadedFile(
        "test.jpg",
        image_io.read(),
        content_type="image/jpeg",
    )


@override_settings(
    AWS_S3_BUCKET_NAME="test-bucket",
    AWS_S3_ACCESS_KEY_ID="testing",
    AWS_S3_SECRET_ACCESS_KEY="testing",
    AWS_S3_REGION="ap-northeast-2",
)
@mock_aws
class MyApplicationListTest(APITestCase):
    def setUp(self) -> None:
        """테스트 케이스 실행 전에 초기 데이터 설정"""
        self.s3 = boto3.client("s3", region_name=settings.AWS_S3_REGION)
        self.s3.create_bucket(
            Bucket=settings.AWS_S3_BUCKET_NAME, CreateBucketConfiguration={"LocationConstraint": settings.AWS_S3_REGION}
        )

        self.user1 = User.objects.create_user(
            email="user1@test.com",
            password="password",
            name="유저1",
            nickname="유저1닉네임",
            phone_number="010-1111-1111",
            gender="M",
            birthday="2000-01-01",
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com",
            password="password",
            name="유저2",
            nickname="유저2닉네임",
            phone_number="010-2222-2222",
            gender="F",
            birthday="1999-01-01",
        )

        aware_start_at = timezone.make_aware(datetime(2025, 1, 1))
        aware_end_at = timezone.make_aware(datetime(2025, 3, 1))

        study_group1 = StudyGroup.objects.create(
            name="테스트 스터디 1", max_headcount=5, start_at=aware_start_at, end_at=aware_end_at
        )
        study_group2 = StudyGroup.objects.create(
            name="테스트 스터디 2", max_headcount=5, start_at=aware_start_at, end_at=aware_end_at
        )

        recruitment1 = Recruitment.objects.create(
            author=self.user2,
            study_group=study_group1,
            title="공고 1",
            content="내용1",
            expected_headcount=3,
            estimated_fee=10000,
        )
        recruitment2 = Recruitment.objects.create(
            author=self.user2,
            study_group=study_group2,
            title="공고 2",
            content="내용2",
            expected_headcount=3,
            estimated_fee=20000,
        )

        # 가상 이미지 업로드 및 URL 생성
        test_image = get_test_image()
        image_key = f"test_images/{test_image.name}"
        self.s3.upload_fileobj(test_image, settings.AWS_S3_BUCKET_NAME, image_key)
        mock_s3_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.amazonaws.com/{image_key}"
        RecruitmentImage.objects.create(recruitment=recruitment2, img_url=mock_s3_url)
        self.mock_s3_url = mock_s3_url

        # user1이 2개의 공고에 지원
        Application.objects.create(recruitment=recruitment1, user=self.user1, motivation="지원1")
        Application.objects.create(recruitment=recruitment2, user=self.user1, motivation="지원2")

        # user2가 1개의 공고에 지원
        Application.objects.create(recruitment=recruitment1, user=self.user2, motivation="지원3")

        self.url = reverse("my-application-list")

    def test_my_applications_list_success(self) -> None:
        """성공: 로그인한 사용자가 자신의 지원 내역 목록을 조회"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"][0]["title"], "공고 2")

        # thumbnail_image_url이 올바르게 나오는지 확인
        self.assertEqual(response.data["results"][0]["thumbnail_image_url"], self.mock_s3_url)
        self.assertIsNone(response.data["results"][1]["thumbnail_image_url"])

    def test_application_isolation(self) -> None:
        """성공: 다른 사용자의 지원 내역이 보이지 않는지 확인"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "공고 1")

    def test_unauthenticated_access_fails(self) -> None:
        """실패: 로그인하지 않은 사용자는 접근 불가"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_pagination(self) -> None:
        """성공: 페이지네이션 동작 확인"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {"limit": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next_cursor"])

        # 다음 페이지 요청
        next_cursor_url = response.data["next_cursor"]
        response2 = self.client.get(next_cursor_url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data["results"]), 1)
        self.assertIsNone(response2.data["next_cursor"])  # 마지막 페이지이므로 next_cursor는 null

    def test_cascade_delete_on_recruitment_deletion(self) -> None:
        """성공: 공고 삭제 시, 관련 지원 내역도 함께 삭제되는지 확인 (CASCADE)"""
        # GIVEN: user1이 지원한 application 객체와 그 ID
        application_to_delete = Application.objects.get(user=self.user1, recruitment__title="공고 1")
        application_id = application_to_delete.id

        # WHEN: 해당 공고를 삭제
        application_to_delete.recruitment.delete()

        # THEN: 해당 application 객체가 더 이상 존재하지 않아야 함
        with self.assertRaises(Application.DoesNotExist):
            Application.objects.get(id=application_id)
