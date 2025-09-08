import boto3 # AWS SDK for Python, 즉 AWS 서비스(S3, EC2, RDS 등)에 접근할 수 있는 라이브러리
import os
import logging # 로깅 시 에러 메시지 출력
import uuid # 고유한 파일 이름 생성을 위한 라이브러리
from botocore.exceptions import ClientError # AWS 서비스 통신 중 에러 발생 시 logging과 함께 사용
import

class S3Uploader:

    def __init__(self):
        '''
        S3에 접근할 client 객체 생성
        환경변수에서 AWS 인증 정보와 버킷 정보를 가져옴
        '''
        self.s3_client = boto3.client(
            's3', # S3 API 호출 객체
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')

    # 프로필 파일 업로드 함수
    def profile_upload(self, file_obj, folder="uploads"):
        '''
        메모리 파일 또는 열려있는 파일 객체를 S3에 업로드
        file_obj: Django InMemoryUploadedFile(open 형태의 파일 객체)
        folder: S3 내 폴더 (기본값: "uploads")
        '''
        ext = os.path.splitext(file_obj.name)[-1] # 파일 확장자 추출 / 예) .pdf, .jpg, .png
        key = f"{folder}/{uuid.uuid4().hex}{ext}" # S3 내 저장될 파일 경로 및 이름 / 예) uploads/uuid4hex.pdf

        # 파일 객체를 S3 버킷에 업로드
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
            )
            return key

        except ClientError as e:
            logging.error(f"failed: {e}")
            return None


