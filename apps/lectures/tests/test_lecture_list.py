import uuid
from typing import cast
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from apps.lectures.models.crawled_lectures import Lecture


class LectureTestCase(TestCase):
    def setUp(self) -> None:
        Lecture.objects.all().delete()

        # Given
        self.client = Client()
        self.list_url = reverse("lectures:lecture_list")
        self.lecture1 = Lecture.objects.create(
            id=1,
            uuid=uuid.uuid4(),
            title="테스트 강의",
            instructor="코딩 파트너",
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
            title="테스s트 강의2",
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
            self.assertEqual(lecture1_data["instructor"], self.lecture2.instructor)
        lecture2_data = next((item for item in results if item["title"] == self.lecture2.title), None)
        self.assertIsNotNone(lecture2_data)
        if lecture2_data is not None:
            self.assertEqual(lecture2_data["instructor"], self.lecture2.instructor)

    def test_search_by_title(self) -> None:
        # When
        response = self.client.get(self.list_url, {"search": "테스트"})

        # Then
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(len(response_data["results"]), 1)  # 길이 대조
        self.assertEqual(response_data["results"][0]["title"], "테스트 강의")  # 제목 대조

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
