import json
import uuid
from typing import Dict, Set, cast
from unittest.mock import MagicMock, patch

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
        fake_redis = mock_redis.return_value
        fake_redis.get.return_value = None  # 캐시 없을 때

        client = Client()
        url = reverse("lectures:lecture_list")

        response = client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
        self.assertGreaterEqual(len(data["results"]), 2)

        # 검색 필터 확인
        titles = [lec["title"] for lec in data["results"]]
        self.assertIn("PyTorch를 활용한 AI 모델 학습", titles)
        self.assertIn("Django로 웹 서비스 만들기", titles)

        # Redis에 캐시 저장 확인
        fake_redis.set.assert_called_once()
