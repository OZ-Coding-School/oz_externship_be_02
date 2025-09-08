import json
import uuid
from typing import Any, Dict, List, Set, cast
from unittest.mock import MagicMock, patch

import redis
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_categories import LectureCategory
from apps.lectures.serializers.crawled_lecture import LectureSerializer
from apps.users.models.user import User


class LectureTestCase(TestCase):
    def setUp(self) -> None:
        # Given
        cache.clear()
        self.client = Client()
        self.url = reverse("lectures:lecture_list")

        self.category_ai = Category.objects.create(name="AI")
        self.category_web = Category.objects.create(name="웹 개발")
        self.category_ds = Category.objects.create(name="데이터 사이언스")
        assert str(self.category_ai) == "AI"
        assert str(self.category_web) == "웹 개발"
        assert str(self.category_ds) == "데이터 사이언스"

        self.lecture1 = Lecture.objects.create(
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
        assert str(self.lecture1) == "PyTorch를 활용한 AI 모델 학습"
        assert str(self.lecture2) == "Django로 웹 서비스 만들기"

        LectureCategory.objects.create(lecture=self.lecture1, category=self.category_ai)
        LectureCategory.objects.create(lecture=self.lecture1, category=self.category_ds)
        LectureCategory.objects.create(lecture=self.lecture2, category=self.category_ds)
        LectureCategory.objects.create(lecture=self.lecture2, category=self.category_web)

    @patch("apps.lectures.views.lecture_list.redis.Redis")  # Redis mocking
    def test_get_lecture_list_success(self, mock_redis: MagicMock) -> None:
        # Given
        fake_redis = mock_redis.return_value
        # When
        fake_redis.get.return_value = None
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Then
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
        self.assertGreaterEqual(len(data["results"]), 2)
        fake_redis.set.assert_called_once()

    @patch("apps.lectures.views.lecture_list.redis.Redis")
    def test_get_lecture_list_with_cache(self, mock_redis: MagicMock) -> None:
        # Given
        fake_redis = mock_redis.return_value
        cached_data = [{"title": "Cached Lecture", "instructor": "Charlie", "updated_at": "2025-09-01"}]
        fake_redis.get.return_value = json.dumps(cached_data)
        # When
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Then
        self.assertEqual(data["results"][0]["title"], "Cached Lecture")

    @patch("apps.lectures.views.lecture_list.redis.Redis")
    def test_redis_connection_error(self, mock_redis: MagicMock) -> None:
        # Given
        fake_redis = mock_redis.return_value
        # When
        fake_redis.get.side_effect = redis.exceptions.ConnectionError
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 500)
        # Then
        self.assertIn("detail", response.json())

    @patch("apps.lectures.views.lecture_list.redis.Redis")
    def test_invalid_cached_data(self, mock_redis: MagicMock) -> None:
        # Given
        fake_redis = mock_redis.return_value
        fake_redis.get.return_value = "{invalid-json}"
        # When
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 500)
        # Then
        self.assertIn("detail", response.json())

    @patch("apps.lectures.views.lecture_list.redis.Redis")
    @patch("apps.lectures.views.lecture_list.Category.objects")
    def test_ordering_and_filtering(self, mock_category_objects: MagicMock, mock_redis: MagicMock) -> None:
        # Given
        fake_redis = mock_redis.return_value
        fake_redis.get.return_value = None
        fake_redis.set.return_value = None

        mock_category_objects.filter.return_value.values_list.return_value = [self.category_ai.id]
        mock_serializer_data = [
            {
                "title": self.lecture1.title,
                "instructor": self.lecture1.instructor,
                "average_rating": self.lecture1.average_rating,
                "original_price": self.lecture1.original_price,
                "updated_at": "2025-09-04T11:27:49.614835+09:00",
                "categories": [self.category_ai.id, self.category_ds.id],  # 중요: categories에 ID 리스트를 포함
            },
            {
                "title": self.lecture2.title,
                "instructor": self.lecture2.instructor,
                "average_rating": self.lecture2.average_rating,
                "original_price": self.lecture2.original_price,
                "updated_at": "2025-09-04T14:27:49.615546+09:00",
                "categories": [self.category_ds.id, self.category_web.id],
            },
        ]
        # Data_Driven
        sorting_test_cases: List[Dict[str, Any]] = [
            {"ordering_param": "price_desc", "expected_title": "Django로 웹 서비스 만들기"},
            {"ordering_param": "price_asc", "expected_title": "PyTorch를 활용한 AI 모델 학습"},
            {"ordering_param": "rating_desc", "expected_title": "PyTorch를 활용한 AI 모델 학습"},
            {"ordering_param": "rating_asc", "expected_title": "Django로 웹 서비스 만들기"},
            {"ordering_param": "oldest", "expected_title": "PyTorch를 활용한 AI 모델 학습"},
            {"ordering_param": "oldest_desc", "expected_title": "Django로 웹 서비스 만들기"},  # default 정렬
            {"ordering_param": "updated_at", "expected_title": "Django로 웹 서비스 만들기"},  # default 정렬
            {"ordering_param": None, "expected_title": "Django로 웹 서비스 만들기"},  # default 정렬
        ]
        with patch.object(LectureSerializer, "data", new=mock_serializer_data):
            for case in sorting_test_cases:
                # When
                ordering_param = case["ordering_param"]
                url = f"{self.url}?search=AI&category=AI"
                if ordering_param:
                    url += f"&ordering={ordering_param}"

                response = self.client.get(url)
                data = response.json()
                # Then
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(data["results"]), 1)
                self.assertEqual(data["results"][0]["title"], "PyTorch를 활용한 AI 모델 학습")

    @patch("apps.lectures.views.lecture_list.LectureListView.paginate")
    @patch("apps.lectures.views.lecture_list.redis.Redis")
    def test_empty_page_scenario(self, mock_redis: MagicMock, mock_paginate: MagicMock) -> None:
        # Given
        fake_redis = mock_redis.return_value
        fake_redis.get.return_value = None
        fake_redis.set.return_value = None
        # When
        mock_paginate.return_value = (None, MagicMock())
        response = self.client.get(self.url)
        data = response.json()
        # Then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["results"], [])
        self.assertIsNone(data["next"])
        self.assertIsNone(data["previous"])

    @patch("apps.lectures.views.lecture_list.redis.Redis")
    def test_invalid_page_number_returns_first_page(self, mock_redis: MagicMock) -> None:
        # Given
        fake_redis = mock_redis.return_value
        fake_redis.get.return_value = None
        fake_redis.set.return_value = None
        # When
        url = f"{self.url}?page=abc"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Then
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 2)

    @patch("apps.lectures.views.lecture_list.redis.Redis")
    def test_out_of_range_page_returns_empty_response(self, mock_redis: MagicMock) -> None:
        # Given
        fake_redis = mock_redis.return_value
        fake_redis.get.return_value = None
        fake_redis.set.return_value = None
        # When
        url = f"{self.url}?page=3"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Then
        self.assertEqual(data["results"], [])
        self.assertIsNone(data["next"])
        self.assertIsNone(data["previous"])
