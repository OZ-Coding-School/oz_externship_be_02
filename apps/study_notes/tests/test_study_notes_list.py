from datetime import datetime
from typing import cast

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import StudyNote
from apps.study_notes.serializers.study_notes_serializers import StudyNoteListSerializer
from apps.users.models.user import User


class StudyNoteListViewTests(TestCase):
    """StudyNoteListView 전체 조회 테스트"""

    client: APIClient

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

        # 스터디 그룹 생성
        cls.study_group = StudyGroup.objects.create(
            name="테스트그룹",
            max_headcount=5,
            start_at=timezone.make_aware(datetime(2025, 9, 16, 12, 0, 0)),
            end_at=timezone.make_aware(datetime(2025, 9, 30, 12, 0, 0)),
        )
        cls.study_group.members.add(cls.user)

        # 테스트용 노트 생성
        cls.note1 = StudyNote.objects.create(
            study_group=cls.study_group,
            author=cls.user,
            title="노트 1",
            content="내용 1",
            ai_summary="요약 1",
        )
        cls.note2 = StudyNote.objects.create(
            study_group=cls.study_group,
            author=cls.user,
            title="노트 2",
            content="내용 2",
            ai_summary="요약 2",
        )

        cls.list_url = reverse("study-notes", kwargs={"group_uuid": str(cls.study_group.uuid)})

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_study_notes_list_success(self) -> None:
        """스터디 그룹 멤버가 스터디 기록 전체 조회"""
        response = cast(Response, self.client.get(self.list_url))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "노트 2")
        self.assertEqual(response.data[1]["title"], "노트 1")
        # 작성자 정보 확인
        self.assertIn("author", response.data[0])
        self.assertEqual(response.data[0]["author"]["nickname"], "nick1")

    def test_study_notes_list_empty(self) -> None:
        """노트가 없는 경우에도 빈 리스트 반환"""
        StudyNote.objects.all().delete()
        response = cast(Response, self.client.get(self.list_url))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_study_notes_permission_denied(self) -> None:
        """스터디 그룹에 속하지 않은 유저 조회 시 403"""
        self.client.force_authenticate(user=self.other_user)
        response = cast(Response, self.client.get(self.list_url))
        self.assertEqual(response.status_code, 403)
