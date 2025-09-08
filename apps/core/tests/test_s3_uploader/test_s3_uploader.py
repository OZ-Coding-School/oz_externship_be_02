import io  # 가짜 파일을 만들기 위해 사용

import boto3  # AWS 와 통신을 하기 위해 사용
from django.test import TestCase
from moto import mock_aws  # 가짜 버킷을 만들기 위해 사용

from apps.core.utils.s3_uploader import S3Uploader


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
        self.s3 = boto3.client("s3", region_name="ap-northeast-2")
        self.s3.create_bucket(Bucket="test-bucket", CreateBucketConfiguration={"LocationConstraint": "ap-northeast-2"})
        self.uploader = S3Uploader(region="ap-northeast-2", bucket="test-bucket", access_key="test", secret_key="test")

    def test_file_exists(self) -> None:
        """
        파일 업로드 후 존재 여부 확인
        """
        file = io.BytesIO(b"test_file")  # b는 바이트 데이터라는 의미
        result = self.uploader.upload_fileobj(file, "test.txt")
        uploaded_key = result["key"]
        file_exists = self.uploader.file_exists(uploaded_key)
        self.assertTrue(file_exists)
