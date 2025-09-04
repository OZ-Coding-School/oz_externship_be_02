from typing import cast

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.study_notes.models.study_notes import StudyNote

from .Mockdata import create_all_mock_data

User = get_user_model()


class TestCode(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        data = create_all_mock_data()
        self.users = data["users"]
        self.groups = data["groups"]
        self.notes = data["notes"]
        self.user = self.users[1]
        self.group = self.groups[1]
        self.client.force_authenticate(user=self.user)
        self.url = reverse("create-study-note", kwargs={"group_uuid": self.group.uuid})

    def test_create_study_note_false(self) -> None:
        """
        필수값에 대한 실패 테스트
        """
        payload = {
            "title": "",
            "content": "오늘은 TDD 작성법에 대해 공부했습니다.",
            "images": ["https://example.com/image1.png"],
            "attachments": [{"file_url": "https://example.com/file1.pdf", "file_name": "file1.pdf"}],
        }
        response = cast(Response, self.client.post(self.url, payload, format="json"))
        print("status:", response.status_code)
        print("request.data 전달된 값:", payload)
        print("response.data:", response.data)
        # 상태 코드 검증
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 응답 데이터 검증
        self.assertEqual(response.data["title"], payload["title"])
        self.assertEqual(response.data["content"], payload["content"])
        self.assertEqual(response.data["ai_summary"], "AI 요약은 추후 자동 생성됩니다.")

        # DB 데이터 검증
        self.assertTrue(StudyNote.objects.filter(title=payload["title"]).exists())

    def test_create_study_note_success(self) -> None:
        """
        스터디 노트 생성 성공 테스트
        """
        payload = {
            "title": "9월 04일 스터디 노트",
            "content": "오늘은 TDD 작성법에 대해 공부했습니다.",
            "images": ["https://example.com/image1.png"],
            "attachments": [{"file_url": "https://example.com/file1.pdf", "file_name": "file1.pdf"}],
        }
        response = cast(Response, self.client.post(self.url, payload, format="json"))
        print("status:", response.status_code)
        print("request.data 전달된 값:", payload)
        print("response.data:", response.data)
        # 상태 코드 검증
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 응답 데이터 검증
        self.assertEqual(response.data["title"], payload["title"])
        self.assertEqual(response.data["content"], payload["content"])
        self.assertEqual(response.data["ai_summary"], "AI 요약은 추후 자동 생성됩니다.")

        # DB 데이터 검증
        self.assertTrue(StudyNote.objects.filter(title=payload["title"]).exists())
