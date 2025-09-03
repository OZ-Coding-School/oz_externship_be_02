from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_bookmarks import LectureBookmark
from apps.users.models.user import User


class BookmarkToggleTest(APITestCase):
    def setUp(self):
        # 테스트용 유저 생성 + 로그인 처리
        self.user = User.objects.create_user(
            email="test@naver.com",
            password="password123",
            name="테스트유저",
            nickname="tester",
            phone_number="01012345678",
            gender="M",
            birthday="2000-01-23",
        )
        self.client.force_authenticate(user=self.user)  # 로그인 된 상태로 요청

        # 테스트용 강의 생성
        self.lecture = Lecture.objects.create(
            title="테스트 강의",
            instructor="효종머왕",
            duration=60,
            difficulty="normal",
            description="테스트스트",
            platform="inflearn",
            original_price=10000,
            discount_price=5000,
            url_link="https://inflearn.com",
        )

        # API URL 세팅
        self.url = "/api/lectures/v1/bookmarks/toggle"

    def test_toggle_bookmark_add(self):
        """북마크가 없을 때 > 추가됨"""
        response = self.client.post(self.url, {"lecture_id": str(self.lecture.pk)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["bookmarked"])
        self.assertTrue(LectureBookmark.objects.filter(user=self.user, lecture=self.lecture).exists())

    def test_toggle_bookmark_remove(self):
        """이미 북마크가 있을 때 → 취소됨"""
        LectureBookmark.objects.create(user=self.user, lecture=self.lecture)

        response = self.client.post(self.url, {"lecture_id": str(self.lecture.pk)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["bookmarked"])
        self.assertFalse(LectureBookmark.objects.filter(user=self.user, lecture=self.lecture).exists())

    def test_toggle_bookmark_invalid_lecture(self):
        """존재하지 않는 lecture_id"""
        response = self.client.post(self.url, {"lecture_id": 99999999}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

    def test_toggle_bookmark_missing_field(self):
        """lecture_id 누락"""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
