from datetime import date
from typing import Any

import boto3
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from moto import mock_aws
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from apps.users.models.user import User


@override_settings(
    AWS_S3_BUCKET_NAME="test-bucket",
    AWS_S3_ACCESS_KEY_ID="fake",  # 아무 값이나 가능
    AWS_S3_SECRET_ACCESS_KEY="fake",
    AWS_S3_REGION="ap-northeast-2",
)
@mock_aws
class RecruitmentFileUploadViewTest(APITransactionTestCase):

    def setUp(self) -> None:
        # moto의 가짜 S3 클라이언트 생성
        self.s3 = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        )
        self.s3.create_bucket(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": settings.AWS_S3_REGION},
        )
        self.user = User.objects.create_user(
            email="test@example.com", password="password123", birthday=date(2000, 1, 1), phone_number="010-1234-5678"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("recruitment-attachments-upload")

    def test_file_upload_success(self) -> None:
        # GIVEN
        test_file = SimpleUploadedFile(name="test.pdf", content=b"file_content", content_type="application/pdf")
        data = {"file": test_file}

        # WHEN
        response = self.client.post(self.url, data=data)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("file_url", response.data)

    def test_file_upload_fail_no_file(self) -> None:
        # GIVEN
        data: dict[str, Any] = {}
        # WHEN
        response = self.client.post(self.url, data=data, format="multipart")
        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
