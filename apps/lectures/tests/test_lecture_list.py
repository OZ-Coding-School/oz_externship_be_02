import uuid
from typing import cast
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_categories import LectureCategory
from apps.lectures.models.categories import Category
from apps.users.models.user import User

class LectureTestCase(TestCase):
    def setUp(self) -> None:

        # Given
        self.category_ai = Category.objects.create(name="AI")
        self.category_web = Category.objects.create(name="웹 개발")
        self.category_ds = Category.objects.create(name="데이터 사이언스")

        self.client = Client()
        self.list_url = reverse("lectures:lecture_list")
        self.lecture1 = Lecture.objects.create(
            id=1,
            uuid=uuid.uuid4(),
            title="PyTorch를 활용한 AI 모델 학습",
            instructor="이코딩",
            average_rating=5.00,
            duration=100,
            difficulty="초급",
            description="PARKCODING",
            platform="유데미",
            original_price=10000,
            discount_price=5000,
            url_link="http://example.com/lecture/1",
            thumbnail_img_url="http://example.com/img.jpg",
            updated_at="2025-09-04T11:27:49.614835+09:00",
        )
        self.lecture2 = Lecture.objects.create(
            id=2,
            uuid=uuid.uuid4(),
            title="Django로 웹 서비스 만들기",
            instructor="코딩 파트너2",
            average_rating=4.00,
            duration=80,
            difficulty="초급",
            description="NOTPARKCODING",
            platform="인프런",
            original_price=20000,
            discount_price=1000,
            url_link="http://example.com/lecture/2",
            thumbnail_img_url="http://example.com/img2.jpg",
            updated_at="2025-09-04T14:27:49.615546+09:00",
        )

        LectureCategory.objects.create(lecture=self.lecture1, category=self.category_ai)
        LectureCategory.objects.create(lecture=self.lecture1, category=self.category_ds)
        LectureCategory.objects.create(lecture=self.lecture2, category=self.category_ds)
        LectureCategory.objects.create(lecture=self.lecture2, category=self.category_web)

    def test_lecture_list_api(self) -> None:
        # When
        response = self.client.get(self.list_url)

        # Then
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        results = response_data["results"]

        self.assertEqual(len(results), 2)  # 길이 대조

        titles = [item["title"] for item in results]  # 제목 대조
        self.assertIn(self.lecture1.title, titles)
        self.assertIn(self.lecture2.title, titles)
        lecture1_data = next((item for item in results if item["title"] == self.lecture1.title), None)
        self.assertIsNotNone(lecture1_data)
        if lecture1_data is not None:
            self.assertEqual(lecture1_data["instructor"], self.lecture1.instructor)
        lecture2_data = next((item for item in results if item["title"] == self.lecture2.title), None)
        self.assertIsNotNone(lecture2_data)
        if lecture2_data is not None:
            self.assertEqual(lecture2_data["instructor"], self.lecture2.instructor)

    def test_search_by_instructor(self) -> None:
        # When
        response = self.client.get(self.list_url, {"search": "이코딩"})

        # Then
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(len(response_data["results"]), 1)  # 길이 대조
        self.assertEqual(response_data["results"][0]["title"], "PyTorch를 활용한 AI 모델 학습")  # 제목 대조

    def test_lecture_list_ordering_by_updated_at(self) -> None:
        # When
        response = self.client.get(self.list_url, {"ordering": "-updated_at"})

        # Then
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["title"], self.lecture2.title)
        self.assertEqual(results[1]["title"], self.lecture1.title)

    def test_lecture_list_ordering_by_price(self) -> None:
        # When
        response = self.client.get(self.list_url, {"ordering": "price_desc"})

        # Then
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["title"], self.lecture2.title)
        self.assertEqual(results[1]["title"], self.lecture1.title)

    def test_lecture_list_ordering_by_rating(self) -> None:
        # When
        response = self.client.get(self.list_url, {"ordering": "rating_desc"})

        # Then
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["title"], self.lecture1.title)
        self.assertEqual(results[1]["title"], self.lecture2.title)

    def test_lecture_to_categories(self):
        expected_mapping = {
            self.lecture1.title: {"AI", "데이터 사이언스"},
            self.lecture2.title: {"웹 개발", "데이터 사이언스"},
        }
        for lecture in [self.lecture1, self.lecture2]:
            category_names = set(lecture.lecturecategory_set.all().values_list("category__name", flat=True))
            self.assertSetEqual(category_names, expected_mapping[lecture.title])

    def test_category_to_lectures(self):
        expected_mapping = {
            "AI": {"PyTorch를 활용한 AI 모델 학습"},
            "데이터 사이언스": {"PyTorch를 활용한 AI 모델 학습", "Django로 웹 서비스 만들기"},
            "웹 개발": {"Django로 웹 서비스 만들기"},
        }
        for category in [self.category_ai, self.category_ds, self.category_web]:
            lecture_titles = set(category.lecturecategory_set.all().values_list("lecture__title", flat=True))
            self.assertSetEqual(lecture_titles, expected_mapping[category.name])

    def test_lecture2_no_wrong_categories(self):
        category_names = self.lecture2.lecturecategory_set.all().values_list("category__name", flat=True)
        self.assertNotIn("AI", category_names)