from datetime import datetime
from typing import List
from uuid import UUID

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import StudyNote
from apps.users.models.user import User


class StudyNoteDeleteViewTests(TestCase):
    """스터디 노트 삭제 API 테스트"""

    client: APIClient
    user: User
    other_user: User
    study_group: StudyGroup
    other_group: StudyGroup
    note1: StudyNote
    note2: StudyNote
    other_note: StudyNote

    @classmethod
    def setUpTestData(cls) -> None:
        # 유저 생성
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

        # 그룹 생성
        cls.study_group = StudyGroup.objects.create(
            name="그룹1",
            max_headcount=5,
            start_at=timezone.make_aware(datetime(2025, 9, 16, 12, 0, 0)),
            end_at=timezone.make_aware(datetime(2025, 9, 30, 12, 0, 0)),
        )
        cls.study_group.members.add(cls.user)

        cls.other_group = StudyGroup.objects.create(
            name="그룹2",
            max_headcount=5,
            start_at=timezone.make_aware(datetime(2025, 9, 16, 12, 0, 0)),
            end_at=timezone.make_aware(datetime(2025, 9, 30, 12, 0, 0)),
        )
        cls.other_group.members.add(cls.other_user)

        # 노트 생성
        cls.note1 = StudyNote.objects.create(
            study_group=cls.study_group, author=cls.user, title="노트1", content="내용1"
        )
        cls.note2 = StudyNote.objects.create(
            study_group=cls.study_group, author=cls.user, title="노트2", content="내용2"
        )
        cls.other_note = StudyNote.objects.create(
            study_group=cls.other_group, author=cls.other_user, title="다른노트", content="내용"
        )

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def get_delete_url(self, group_uuid: UUID, note_id: int) -> str:
        return reverse("study-note-detail", kwargs={"group_uuid": str(group_uuid), "note_id": note_id})

    def test_delete_single_note_success(self) -> None:
        """작성자 단일 노트 삭제 성공"""
        response = self.client.delete(self.get_delete_url(self.study_group.uuid, self.note1.id), data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(StudyNote.objects.filter(id=self.note1.id).exists())
        self.assertEqual(response.data["deleted_count"], 1)
        self.assertEqual(response.data["requested_ids"], [self.note1.id])

    def test_delete_multiple_notes_success(self) -> None:
        """작성자 다중 노트 삭제 성공"""
        note_ids: List[int] = [self.note1.id, self.note2.id]
        response = self.client.delete(
            self.get_delete_url(self.study_group.uuid, self.note1.id),
            data={"note_ids": note_ids},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(StudyNote.objects.filter(id__in=note_ids).exists())
        self.assertEqual(response.data["deleted_count"], 2)
        self.assertEqual(response.data["requested_ids"], note_ids)

    def test_delete_unauthorized_user(self) -> None:
        """작성자가 아닌 유저 삭제 시도"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.get_delete_url(self.study_group.uuid, self.note1.id), data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(StudyNote.objects.filter(id=self.note1.id).exists())

    def test_delete_other_group_note(self) -> None:
        """다른 그룹 노트 삭제 시도"""
        response = self.client.delete(self.get_delete_url(self.other_group.uuid, self.other_note.id), data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(StudyNote.objects.filter(id=self.other_note.id).exists())
