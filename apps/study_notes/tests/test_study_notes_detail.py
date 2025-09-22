from datetime import datetime
from typing import cast

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import StudyNote
from apps.users.models.user import User


class StudyNoteDetailViewTests(TestCase):
    """StudyNoteDetailView 테스트"""

    client: APIClient

    def setUp(self) -> None:
        self.client = APIClient()

        # 유저 생성
        self.user = User.objects.create_user(
            email="user1@example.com",
            password="password123",
            name="테스트유저1",
            nickname="nick1",
            phone_number="01012345671",
            gender="남성",
            birthday="2000-01-01",
        )
        self.other_user = User.objects.create_user(
            email="user2@example.com",
            password="password123",
            name="테스트유저2",
            nickname="nick2",
            phone_number="01012345672",
            gender="여성",
            birthday="2000-01-02",
        )

        # 스터디 그룹 생성
        self.study_group = StudyGroup.objects.create(
            name="테스트그룹",
            max_headcount=5,
            start_at=timezone.make_aware(datetime(2025, 9, 16, 12, 0, 0)),
            end_at=timezone.make_aware(datetime(2025, 9, 30, 12, 0, 0)),
        )
        self.study_group.members.add(self.user)

        # 테스트용 노트 생성
        self.note = StudyNote.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="테스트 노트",
            content="테스트 내용",
        )

        self.client.force_authenticate(user=self.user)

    def test_retrieve_study_note_success(self) -> None:
        """스터디 노트 상세 조회 성공"""
        url = reverse("study-note-detail", kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id})
        response = cast(Response, self.client.get(url))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "테스트 노트")
        self.assertEqual(response.data["author"]["nickname"], "nick1")
        # Check if created_at is in the correct format
        self.assertIn(datetime.now().strftime("%Y-%m-%d"), response.data["created_at"])

    def test_retrieve_non_existent_note(self) -> None:
        """존재하지 않는 스터디 노트 조회"""
        url = reverse("study-note-detail", kwargs={"group_uuid": str(self.study_group.uuid), "note_id": 9999})
        response = cast(Response, self.client.get(url))

        self.assertEqual(response.status_code, 404)

    def test_retrieve_note_permission_denied(self) -> None:
        """다른 그룹의 스터디 노트 조회"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("study-note-detail", kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id})
        response = cast(Response, self.client.get(url))

        self.assertEqual(response.status_code, 403)
