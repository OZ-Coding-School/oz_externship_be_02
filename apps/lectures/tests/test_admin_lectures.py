from rest_framework import status
from rest_framework.test import APITestCase

from apps.lectures.models.crawled_lectures import Lecture
from apps.users.models.user import User


class TestAdminLectureList(APITestCase):
    def setUp(self) -> None:
        # 일반 유저
        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass1234",
            name="유저",
            nickname="user",
            phone_number="01000000000",
            gender="M",
            birthday="2000-01-01",
        )
        # 관리자 유저
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="pass1234",
            name="관리자",
            nickname="admin",
            phone_number="01011112222",
            gender="M",
            birthday="1999-12-31",
            is_staff=True,
        )
        self.url = "/api/v1/lectures/admin/lectures"

    def test_auth_required(self) -> None:
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_only(self) -> None:
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_ok(self) -> None:
        # 데이터
        Lecture.objects.create(
            title="Github Mastery",
            instructor="효종 조교",
            duration=60,
            difficulty="normal",
            description="깃허브",
            platform="Inflearn",
            original_price=10000,
            discount_price=5000,
            url_link="https://inflearn.com/github",
            thumbnail_img_url="github.png",
        )
        Lecture.objects.create(
            title="Django REST Framework",
            instructor="머용코치",
            duration=120,
            difficulty="normal",
            description="DRF",
            platform="Inflearn",
            original_price=20000,
            discount_price=15000,
            url_link="https://inflearn.com/django-rest",
            thumbnail_img_url="drf.png",
        )

        self.client.force_authenticate(user=self.admin)
        res = self.client.get(self.url, data={"limit": 1, "offset": 0})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)
        self.assertIn("results", res.data)
        self.assertEqual(len(res.data["results"]), 1)

        # 검색
        res_search = self.client.get(self.url, data={"search": "django"})
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        titles = [item["title"] for item in res_search.data["results"]]
        self.assertTrue(any("Django" in t for t in titles))
