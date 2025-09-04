from rest_framework import status
from rest_framework.test import APITestCase

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_bookmarks import LectureBookmark
from apps.users.models.user import User


class TestBookmarkAddCancel(APITestCase):
    def setUp(self):
        # 사용자 생성 & 인증
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="테스트유저",
            nickname="tester",
            phone_number="01012345678",
            gender="M",
            birthday="2000-01-01",
        )
        self.client.force_authenticate(user=self.user)

        # 강의 생성
        self.lecture = Lecture.objects.create(
            title="테스트 강의",
            instructor="홍길동",
            duration=60,
            difficulty="normal",
            description="설명",
            platform="udemy",
            original_price=10000,
            discount_price=5000,
            url_link="https://example.com",
        )

        base = "/api/v1/lectures"
        self.add_url = f"{base}/{self.lecture.pk}/bookmarks/add"
        self.cancel_url = f"{base}/{self.lecture.pk}/bookmarks/cancel"

    def test_add_bookmark(self):
        res = self.client.post(self.add_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("lecture_id"), self.lecture.pk)
        self.assertTrue(res.data.get("bookmarked"))
        self.assertTrue(LectureBookmark.objects.filter(user=self.user, lecture=self.lecture).exists())

    def test_cancel_bookmark(self):
        LectureBookmark.objects.create(user=self.user, lecture=self.lecture)
        res = self.client.delete(self.cancel_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("lecture_id"), self.lecture.pk)
        self.assertFalse(res.data.get("bookmarked"))
        self.assertFalse(LectureBookmark.objects.filter(user=self.user, lecture=self.lecture).exists())

    def test_add_invalid_lecture(self):
        res = self.client.post("/api/v1/lectures/999999/bookmarks/add")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", res.data)

    def test_cancel_invalid_lecture(self):
        res = self.client.delete("/api/v1/lectures/999999/bookmarks/cancel")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", res.data)
