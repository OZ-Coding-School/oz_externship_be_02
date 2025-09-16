import logging
import uuid
from typing import Any, BinaryIO, Callable

import boto3  # AWS 와 통신을 하기 위한 라이브러리
from botocore.exceptions import ClientError  # S3 에러 처리
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from rest_framework.exceptions import APIException, NotFound

if not settings.DEBUG:
    logger = logging.getLogger("django")
else:
    logger = logging.getLogger("django.server")


class S3Uploader:
    """
    S3에 파일을 업로드하는 클래스
    """

    def __init__(self, region: str = settings.AWS_S3_REGION, bucket: str = settings.AWS_S3_BUCKET_NAME) -> None:
        """
        S3 클라이언트 초기화
        boto3 S3 클라이언트 생성
        region, bucket, access_key, secret_key를 받아 내부 변수에 저장
        """
        self.bucket_name = bucket
        self.s3_client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        )

    def s3_safe_call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        S3 API 호출을 안전하게 실행하고 예외를 처리하는 래퍼 함수.

        :param func: boto3 S3 클라이언트 메서드 (예: s3_client.head_object)
        :param args: 함수에 전달할 위치 인자
        :param kwargs: 함수에 전달할 키워드 인자
        :return: 성공 시 boto3 응답(dict), 실패 시 APIException 예외 발생
        """
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            # 자주 쓰이는 에러 코드 분기 처리
            if error_code in ("NoSuchKey", "404"):
                error_message = f"S3 object not found."
                logger.warning(error_message)
                raise NotFound(error_message)

            error_message = f"Unexpected S3 error: {e}"
            logger.error(error_message)
            raise APIException(error_message)

        except Exception as e:
            error_message = f"Unknown error during S3 operation: {e}"
            logger.exception(error_message)
            raise APIException(error_message)

    def upload_file(self, file: BinaryIO | UploadedFile) -> dict[str, str]:
        """
        S3에 파일 업로드 (예외 처리 포함)
        """
        key = file.name if isinstance(file, UploadedFile) else str(uuid.uuid4())
        key = cast(str, key)
        self.s3_safe_call(func=self.s3_client.upload_fileobj, Fileobj=file, Bucket=self.bucket_name, Key=key)
        return {"url": f"s3://{self.bucket_name}/{key}", "key": key}

    def file_exists(self, key: str) -> bool:
        self.s3_safe_call(func=self.s3_client.head_object, Bucket=self.bucket_name, Key=key)
        return True

    def delete_file(self, key: str) -> bool:
        """
        S3에 파일 삭제 (예외 처리 포함)
        """
        self.s3_safe_call(func=self.s3_client.delete_object, Bucket=self.bucket_name, Key=key)
        return True
