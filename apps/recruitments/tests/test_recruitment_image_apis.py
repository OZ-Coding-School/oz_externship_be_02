from datetime import date
from io import BytesIO

import boto3
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from moto import mock_aws
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient, APITransactionTestCase

User = get_user_model()


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
    AWS_S3_ACCESS_KEY_ID="fake",  # 아무 값이나 가능
    AWS_S3_SECRET_ACCESS_KEY="fake",
    AWS_S3_REGION="ap-northeast-2",
)
@mock_aws
class RecruitmentImageUploadAPITest(APITransactionTestCase):
    # 여기에 이미지 업로드 view 테스트작성해보기
    def setUp(self) -> None:
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
            email="test@example.com",
            password="password0314",
            nickname="해파리볶음밥",
            birthday=date(2002, 3, 14),
            phone_number="010-1111-1111",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("recruitment-images-upload")

    def test_upload_image_success(self) -> None:
        response = self.client.post(
            self.url,
            {"image": get_test_image()},
            format="multipart",
        )

        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image_url", response.data)

        bucket_objects = self.s3.list_objects(Bucket="test-bucket").get("Contents", [])
        self.assertTrue(any(obj["Key"] for obj in bucket_objects))

    def test_upload_image_without_file(self) -> None:
        response = self.client.post(self.url, {}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)
