from rest_framework import status
from rest_framework.test import APITestCase

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_bookmarks import LectureBookmark
from apps.users.models.user import User


class TestBookmarkView(APITestCase):
    def setUp(self) -> None:
        # 사용자 생성,인증
        self.user = User.objects.create_user(
            email="test@naver.com",
            password="password123",
            name="테스트유저",
            nickname="tester",
            phone_number="01012345678",
            gender="M",
            birthday="2000-01-01",
        )
        self.client.force_authenticate(user=self.user)

        # 강의 생성 (Lecture는 UUIDBaseModel을 상속 → uuid 필드 사용)
        self.lecture = Lecture.objects.create(
            title="테스트 강의",
            instructor="효종",
            duration=60,
            difficulty="normal",
            description="설명",
            platform="Inflearn",
            original_price=10000,
            discount_price=5000,
            url_link="https://Inflearn.com",
        )

        base = "/api/v1/lectures"
        # URL 컨버터가 <uuid:lecture_uuid> 라서 pk가 아닌 uuid를 사용
        self.lecture_uuid_str = str(self.lecture.uuid)
        self.add_url = f"{base}/{self.lecture_uuid_str}/bookmark"
        self.cancel_url = f"{base}/{self.lecture_uuid_str}/bookmark"

    def test_add_bookmark_success(self) -> None:
        """북마크 추가 성공"""
        res = self.client.post(self.add_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("lecture_uuid"), self.lecture_uuid_str)
        self.assertTrue(res.data.get("bookmarked"))
        self.assertTrue(LectureBookmark.objects.filter(user=self.user, lecture=self.lecture).exists())

    def test_add_bookmark_idempotent(self) -> None:
        """이미 북마크된 강의도 성공"""
        self.client.post(self.add_url)
        res = self.client.post(self.add_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get("bookmarked"))

    def test_delete_bookmark_success(self) -> None:
        """북마크 해제 성공"""
        self.client.post(self.add_url)
        res = self.client.delete(self.cancel_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("lecture_uuid"), self.lecture_uuid_str)
        self.assertFalse(res.data.get("bookmarked"))
        self.assertFalse(LectureBookmark.objects.filter(user=self.user, lecture=self.lecture).exists())

    def test_delete_bookmark_idempotent(self) -> None:
        """북마크가 없어도 성공"""
        res = self.client.delete(self.cancel_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data.get("bookmarked"))

    def test_add_invalid_lecture(self) -> None:
        """존재하지 않는 강의 추가 시 404"""
        res = self.client.post("/api/v1/lectures/00000000-0000-0000-0000-000000000000/bookmark")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_invalid_lecture(self) -> None:
        """존재하지 않는 강의 삭제 시 404"""
        res = self.client.delete("/api/v1/lectures/00000000-0000-0000-0000-000000000000/bookmark")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_requires_authentication(self) -> None:
        """로그인하지 않으면 401"""
        self.client.force_authenticate(user=None)
        res_post = self.client.post(self.add_url)
        res_delete = self.client.delete(self.cancel_url)
        self.assertEqual(res_post.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res_delete.status_code, status.HTTP_401_UNAUTHORIZED)
