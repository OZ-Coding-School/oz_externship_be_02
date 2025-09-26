from datetime import datetime
from typing import Any, cast
from unittest.mock import patch

import boto3
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from moto import mock_aws
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.utils.s3_uploader import S3Uploader
from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import (
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.study_notes.services.study_notes_services import StudyNoteService
from apps.users.models.user import User


@override_settings(
    AWS_S3_BUCKET_NAME="test-bucket",
    AWS_S3_ACCESS_KEY_ID="fake",
    AWS_S3_SECRET_ACCESS_KEY="fake",
    AWS_S3_REGION="ap-northeast-2",
)
class StudyNoteUpdateWithS3TestCase(TestCase):
    client: APIClient
    user: User
    other_user: User
    study_group: StudyGroup
    note: StudyNote
    image1: StudyNoteImage
    attachment1: StudyNoteAttachment
    service: StudyNoteService
    s3_client: Any
    mock_s3: Any

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Moto S3 Mock 시작
        cls.mock_s3 = mock_aws()
        cls.mock_s3.start()

        # S3 클라이언트 생성 및 버킷 생성
        cls.s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        )
        cls.s3_client.create_bucket(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": settings.AWS_S3_REGION},
        )

        # 유저 & 그룹 생성
        cls.user = User.objects.create_user(
            email="user1@example.com",
            password="password123",
            name="테스트유저1",
            nickname="nick1",
            phone_number="01012345671",
            gender="남성",
            birthday="2000-01-01",
        )
        cls.other_user = User.objects.create_user(
            email="user2@example.com",
            password="password123",
            name="테스트유저2",
            nickname="nick2",
            phone_number="01012345672",
            gender="여성",
            birthday="2000-01-02",
        )
        cls.study_group = StudyGroup.objects.create(
            name="테스트그룹",
            max_headcount=5,
            start_at=timezone.make_aware(datetime(2025, 9, 16, 12, 0, 0)),
            end_at=timezone.make_aware(datetime(2025, 9, 30, 12, 0, 0)),
        )
        cls.study_group.members.add(cls.user)

        # 스터디 노트 + 기존 이미지/첨부
        cls.note = StudyNote.objects.create_note(
            author=cls.user, study_group=cls.study_group, title="노트 1", content="내용 1"
        )
        cls.image1 = cls.note.images.create(img_url="https://fake-s3.com/image1.png")
        cls.attachment1 = cls.note.attachments.create(file_name="file1.pdf", file_url="https://fake-s3.com/file1.pdf")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.mock_s3.stop()
        super().tearDownClass()

    def setUp(self) -> None:
        self.client = APIClient()
        self.service = StudyNoteService(s3_uploader=S3Uploader())
        self.note.refresh_from_db()

    # 정상 수정 (기존 이미지 유지 + 새 이미지/첨부 추가)
    @patch("apps.study_notes.services.study_notes_services.generate_study_summary", return_value="MOCKED SUMMARY")
    def test_normal_update_with_files(self, mock_summary: Any) -> None:
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "study-note-detail",
            kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id},
        )

        data = {
            "title": "수정된 제목",
            "content": "수정된 본문",
        }

        # 기존 이미지/첨부 유지
        # 새 이미지/첨부를 DB에 직접 추가
        self.note.images.create(img_url="https://fake-s3.com/new_img.png")
        self.note.attachments.create(file_name="new_file.pdf", file_url="https://fake-s3.com/new_file.pdf")

        response = self.client.patch(url, data, format="json")
        self.note.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.note.title, "수정된 제목")
        self.assertEqual(self.note.content, "수정된 본문")
        self.assertEqual(self.note.ai_summary, "MOCKED SUMMARY")
        self.assertEqual(self.note.images.count(), 2)
        self.assertEqual(self.note.attachments.count(), 2)

    # 기존 파일 삭제 테스트 (요청에 없는 파일 삭제)
    @patch("apps.study_notes.services.study_notes_services.generate_study_summary", return_value="SUMMARY2")
    def test_update_removes_old_files(self, mock_summary: Any) -> None:
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "study-note-detail",
            kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id},
        )

        data = {
            "title": "수정 후 제목",
            "content": "수정 후 내용",
        }

        # 기존 이미지/첨부 삭제 후 새 파일 추가
        self.note.images.all().delete()
        self.note.attachments.all().delete()
        new_image = self.note.images.create(img_url="https://fake-s3.com/new_img.png")
        new_attachment = self.note.attachments.create(
            file_name="new_file.pdf", file_url="https://fake-s3.com/new_file.pdf"
        )

        response = self.client.patch(url, data, format="json")
        self.note.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.note.title, "수정 후 제목")
        self.assertEqual(self.note.content, "수정 후 내용")
        self.assertEqual(self.note.ai_summary, "SUMMARY2")
        self.assertEqual(self.note.images.count(), 1)
        self.assertEqual(self.note.attachments.count(), 1)

        image = cast(StudyNoteImage, self.note.images.first())
        self.assertEqual(image.img_url, "https://fake-s3.com/new_img.png")
        attachment = cast(StudyNoteAttachment, self.note.attachments.first())
        self.assertEqual(attachment.file_url, "https://fake-s3.com/new_file.pdf")

    # 권한 없는 유저
    def test_update_unauthorized_user(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        url = reverse(
            "study-note-detail",
            kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id},
        )

        data = {"title": "권한 없는 수정"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, "노트 1")
        self.assertEqual(self.note.content, "내용 1")
