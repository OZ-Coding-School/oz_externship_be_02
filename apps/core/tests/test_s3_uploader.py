import io  # 가짜 파일을 만들기 위해 사용

from django.test import TestCase, override_settings
from moto import mock_aws  # 가짜 버킷을 만들기 위해 사용
from rest_framework.exceptions import APIException

from apps.core.utils.s3_uploader import S3Uploader


@override_settings(
    AWS_S3_BUCKET_NAME="test-bucket",
    AWS_S3_ACCESS_KEY_ID="fake",  # 아무 값이나 가능
    AWS_S3_SECRET_ACCESS_KEY="fake",
    AWS_S3_REGION="ap-northeast-2",
)
@mock_aws
class TestS3Uploader(TestCase):
    """
    업로드 후 파일 존재 여부 확인
    """

    def setUp(self) -> None:
        """
        테스트를 위한 가짜 S3 버킷 생성(moto 사용)
        boto3 클라이언트 초기화
        """
        bucket = "test-bucket"
        region = "ap-northeast-2"
        self.s3_uploader = S3Uploader()
        self.s3_uploader.s3_client.create_bucket(
            Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": region}
        )

    def test_upload_file(self) -> None:
        """
        파일 업로드 테스트
        """
        file = io.BytesIO(b"test_file")
        file.name = "test.txt"
        result = self.s3_uploader.upload_file(file)
        self.assertTrue(isinstance(result, dict))
        self.assertIn("key", result)
        self.assertIn("url", result)

    def test_file_exists(self) -> None:
        """
        파일 업로드 후 존재 여부 확인
        """
        file = io.BytesIO(b"test_file")
        file.name = "test.txt"
        result = self.s3_uploader.upload_file(file)
        self.assertTrue(isinstance(result, dict))
        uploaded_key = result["key"]
        file_exists = self.s3_uploader.file_exists(uploaded_key)
        self.assertTrue(file_exists)

    def test_file_not_exists(self) -> None:
        """
        존재하지 않는 파일 확인
        """
        self.assertFalse(self.s3_uploader.file_exists("non_existent_file.txt"))

    def test_delete_file(self) -> None:
        """
        파일 업로드 후 파일 삭제
        """
        file = io.BytesIO(b"test_file")
        file.name = "test.txt"
        result = self.s3_uploader.upload_file(file)
        self.assertTrue(isinstance(result, dict))
        uploaded_key = result["key"]
        deleted = self.s3_uploader.delete_file(uploaded_key)
        self.assertTrue(deleted)

    def test_delete_files(self) -> None:
        """
        여러 파일 업로드 후 delete_files로 삭제
        """
        uploaded_keys = []
        for i in range(1, 4):
            file = io.BytesIO(b"test_file")
            file.name = f"test{i}.txt"
            result = self.s3_uploader.upload_file(file)
            uploaded_keys.append(result["key"])

        self.s3_uploader.delete_files(uploaded_keys)
        for key in uploaded_keys:
            self.assertFalse(self.s3_uploader.file_exists(key))
