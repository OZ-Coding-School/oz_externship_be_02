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
            thumbnail_img_url="https://example.com/thumb1.jpg",
        )

        # URL 컨버터가 <uuid:lecture_uuid> 라서 pk가 아닌 uuid를 사용
        base = "/api/v1/lectures"
        self.lecture_uuid_str = str(self.lecture.uuid)
        self.add_url = f"{base}/{self.lecture_uuid_str}/bookmark"
        self.cancel_url = f"{base}/{self.lecture_uuid_str}/bookmark"
        self.list_url = f"{base}/bookmarks"

    # 추가/삭제 테스트

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

    # 목록 조회 테스트 (REQ-LECT-006)

    def test_list_bookmarks_empty_returns_200(self) -> None:
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("count"), 0)
        self.assertEqual(res.data.get("results"), [])

    def test_list_bookmarks_basic_fields_and_transform(self) -> None:
        lec = Lecture.objects.create(
            title="파이썬 심화",
            instructor="Alice",
            duration=125,
            difficulty="normal",  # 응답에서 MIDDLE로 변환
            description="심화",
            platform="Inflearn",
            original_price=20000,
            discount_price=15000,
            url_link="https://example.com/python-advanced",
            thumbnail_img_url="https://example.com/thumb2.jpg",
        )
        LectureBookmark.objects.create(user=self.user, lecture=lec)

        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("count"), 1)
        self.assertEqual(len(res.data.get("results")), 1)

        item = res.data["results"][0]
        self.assertEqual(item["title"], "파이썬 심화")
        self.assertEqual(item["instructor"], "Alice")
        self.assertEqual(item["platform"], "Inflearn")
        self.assertEqual(item["url_link"], "https://example.com/python-advanced")
        self.assertEqual(item["duration_hhmm"], "02:05")
        self.assertEqual(item["difficulty"], "MIDDLE")
        self.assertIn("thumbnail_img_url", item)
        self.assertIn("original_price", item)
        self.assertIn("discount_price", item)

    def test_list_bookmarks_pagination(self) -> None:
        for i in range(12):
            lec = Lecture.objects.create(
                title=f"강의 {i}",
                instructor="멘토",
                duration=30 + i,
                difficulty="normal",
                description="설명",
                platform="Inflearn",
                original_price=10000 + i,
                discount_price=9000 + i,
                url_link=f"https://example.com/lec-{i}",
                thumbnail_img_url=f"https://example.com/thumb-{i}.jpg",
            )
            LectureBookmark.objects.create(user=self.user, lecture=lec)

        res1 = self.client.get(self.list_url)  # page=1
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data.get("count"), 12)
        self.assertEqual(len(res1.data.get("results")), 10)

        res2 = self.client.get(self.list_url, data={"page": 2})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data.get("count"), 12)
        self.assertEqual(len(res2.data.get("results")), 2)

    def test_list_bookmarks_search(self) -> None:
        lec1 = Lecture.objects.create(
            title="Django 입문",
            instructor="Alice",
            duration=50,
            difficulty="normal",
            description="Django",
            platform="Inflearn",
            original_price=10000,
            discount_price=8000,
            url_link="https://example.com/dj",
            thumbnail_img_url="https://example.com/thumb-dj.jpg",
        )
        lec2 = Lecture.objects.create(
            title="리액트 마스터",
            instructor="Bob",
            duration=70,
            difficulty="normal",
            description="React",
            platform="Inflearn",
            original_price=12000,
            discount_price=9000,
            url_link="https://example.com/react",
            thumbnail_img_url="https://example.com/thumb-react.jpg",
        )
        LectureBookmark.objects.create(user=self.user, lecture=lec1)
        LectureBookmark.objects.create(user=self.user, lecture=lec2)

        # 제목 검색
        res_title = self.client.get(self.list_url, data={"search": "django"})
        self.assertEqual(res_title.status_code, status.HTTP_200_OK)
        self.assertEqual(res_title.data.get("count"), 1)
        self.assertEqual(res_title.data["results"][0]["title"], "Django 입문")

        # 강사 검색
        res_instructor = self.client.get(self.list_url, data={"search": "bob"})
        self.assertEqual(res_instructor.status_code, status.HTTP_200_OK)
        self.assertEqual(res_instructor.data.get("count"), 1)
        self.assertEqual(res_instructor.data["results"][0]["instructor"], "Bob")

    def test_list_requires_authentication(self) -> None:
        """목록 조회도 인증 필요"""
        self.client.force_authenticate(user=None)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
