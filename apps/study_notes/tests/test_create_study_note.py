from datetime import datetime
from typing import Any

import boto3
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from moto import mock_aws

from apps.core.utils.create_temp_image import create_temp_image
from apps.core.utils.s3_uploader import S3Uploader
from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import StudyNote
from apps.study_notes.services.study_notes_services import StudyNoteService
from apps.users.models.user import User


@override_settings(
    AWS_S3_BUCKET_NAME="test-bucket",
    AWS_S3_ACCESS_KEY_ID="fake",
    AWS_S3_SECRET_ACCESS_KEY="fake",
    AWS_S3_REGION="ap-northeast-2",
)
@mock_aws
class StudyNoteServiceTest(TestCase):
    """StudyNoteService.create_study_note 관련 테스트"""

    def setUp(self) -> None:
        # S3 가짜 클라이언트 + 버킷
        self.s3_uploader = S3Uploader(bucket=settings.AWS_S3_BUCKET_NAME)
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        )
        self.s3_client.create_bucket(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": settings.AWS_S3_REGION},
        )

        # 유저 & 그룹 생성
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            name="테스트유저",
            nickname="testnick",
            phone_number="01012345678",
            gender="남성",
            birthday="2000-01-01",
        )
        self.study_group = StudyGroup.objects.create(
            name="테스트그룹",
            max_headcount=5,
            start_at=timezone.make_aware(datetime(2025, 9, 16, 12, 0, 0)),
            end_at=timezone.make_aware(datetime(2025, 9, 30, 12, 0, 0)),
        )

    def test_create_note_success(self) -> None:
        """이미지 + 첨부파일 정상 업로드 후 DB 생성
        예시: S3와 DB에 정상적으로 데이터가 올라가는지 확인
        """
        service = StudyNoteService(s3_uploader=self.s3_uploader)
        image_file = create_temp_image()
        attachment_file = SimpleUploadedFile("test.txt", b"hello world", content_type="text/plain")

        note = service.create_study_note(
            author=self.user,
            study_group=self.study_group,
            title="서비스 테스트 노트",
            content="서비스 테스트 본문",
            images=[image_file],
            attachments=[attachment_file],
        )

        self.assertEqual(note.title, "서비스 테스트 노트")
        self.assertEqual(note.images.count(), 1)
        self.assertEqual(note.attachments.count(), 1)
        attachment = note.attachments.first()
        assert attachment is not None
        self.assertEqual(attachment.file_name, "test.txt")

        image = note.images.first()
        assert image is not None
        self.assertTrue(self.s3_uploader.file_exists(image.img_url.split("/")[-1]))
        self.assertTrue(self.s3_uploader.file_exists(attachment.file_url.split("/")[-1]))

    def test_s3_upload_rolls_back(self) -> None:
        """S3 업로드 실패 시 DB와 S3 모두 롤백
        예시: 업로드 중 실패 발생 시 DB에 노트가 생성되지 않고 S3 업로드도 삭제되는지 테스트
        """
        service = StudyNoteService(s3_uploader=self.s3_uploader)
        image_file = create_temp_image()

        # S3Uploader를 강제로 실패하게 monkey patch
        original_upload = service.s3.upload_file

        def fail_upload(f: Any) -> None:
            raise RuntimeError("강제 업로드 실패")

        setattr(service.s3, "upload_file", fail_upload)

        with self.assertRaises(RuntimeError):
            service.create_study_note(
                author=self.user,
                study_group=self.study_group,
                title="실패 테스트",
                content="본문",
                images=[image_file],
            )

        setattr(service.s3, "upload_file", original_upload)

    def test_db_rolls_back_s3(self) -> None:
        """DB 생성 실패 시 업로드된 S3 파일 삭제 확인
        예시: DB 트랜잭션 에러 발생 시 업로드된 S3 객체가 삭제되는지 확인
        """
        service = StudyNoteService(s3_uploader=self.s3_uploader)
        image_file = create_temp_image()

        # DB 생성 함수 강제 실패
        original_create_note = StudyNote.objects.create_note

        def fail_db(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("DB 실패")

        setattr(StudyNote.objects, "create_note", fail_db)

        with self.assertRaises(RuntimeError):
            service.create_study_note(
                author=self.user,
                study_group=self.study_group,
                title="DB 실패 테스트",
                content="본문",
                images=[image_file],
            )

        setattr(StudyNote.objects, "create_note", original_create_note)
