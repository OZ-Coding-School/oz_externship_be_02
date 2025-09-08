import uuid
from typing import BinaryIO, Dict

import boto3  # AWS 와 통신을 하기 위한 라이브러리
from botocore.exceptions import ClientError  # S3 에러 처리


class S3Uploader:
    """
    S3에 파일을 업로드하는 클래스
    """

    def __init__(self, region: str, bucket: str, access_key: str, secret_key: str):
        """
        S3 클라이언트 초기화
        boto3 S3 클라이언트 생성
        region, bucket, access_key, secret_key를 받아 내부 변수에 저장
        """
        self.region = region
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key

        self.s3_client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def create_file(self, filename: str) -> str:
        """
        가짜 파일 생성
        """
        return f"{uuid.uuid4()}_{filename}"

    def upload_fileobj(self, file: BinaryIO, filename: str) -> Dict[str, str]:
        """
        만들어진 파일을 S3에 업로드
        """
        key = self.create_file(filename)
        self.s3_client.upload_fileobj(Fileobj=file, Bucket=self.bucket, Key=key)
        return {"key": key, "url": f"s3://{self.bucket}/{key}"}

    def file_exists(self, key: str) -> bool:
        """
        S3에 파일이 존재하는지 확인
        """
        self.s3_client.head_object(Bucket=self.bucket, Key=key)
        return True

