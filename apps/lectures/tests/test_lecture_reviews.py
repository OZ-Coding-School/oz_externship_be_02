import json
import uuid
from unittest.mock import MagicMock, patch

import redis
from django.test import Client, TestCase
from django.urls import reverse

from apps.lectures.models.crawled_lecture_reviews import LectureReview
from apps.lectures.models.crawled_lectures import Lecture


class LectureReviewTestCase(TestCase):
    def setUp(self) -> None:

        self.lecture = Lecture.objects.create(
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
        # 리뷰 샘플
        self.review1 = LectureReview.objects.create(
            lecture=self.lecture, content="Great lecture!", rating="5_OUT_OF_5_STARS"
        )
        self.review2 = LectureReview.objects.create(
            lecture=self.lecture, content="Needs improvement", rating="5_OUT_OF_5_STARS"
        )
        assert str(self.review1) == f"{self.lecture.title} 리뷰"
        assert str(self.review2) == f"{self.lecture.title} 리뷰"
        self.client = Client()
        self.url = reverse("lectures:lecture_reviews", kwargs={"lecture_uuid": self.lecture.uuid})

    @patch("apps.lectures.views.lecture_reviews.redis.Redis")
    def test_get_reviews_from_cache(self, mock_redis: MagicMock) -> None:
        # 캐시된 데이터 준비
        cached_reviews = [{"lecture": str(self.lecture.uuid), "content": "Cached review", "rating": 5}]
        fake_redis = mock_redis.return_value
        fake_redis.get.return_value = json.dumps(cached_reviews)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], cached_reviews)
        fake_redis.get.assert_called_once_with(f"lectures:reviews:{self.lecture.uuid}")

    @patch("apps.lectures.views.lecture_reviews.redis.Redis")
    def test_get_reviews_from_db_when_cache_missing(self, mock_redis: MagicMock) -> None:
        fake_redis = mock_redis.return_value
        fake_redis.get.return_value = None  # 캐시 없음
        fake_redis.set.return_value = True

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["content"], self.review1.content)
        self.assertEqual(results[1]["content"], self.review2.content)
        fake_redis.set.assert_called_once()  # DB 조회 후 캐시 저장 확인

    @patch("apps.lectures.views.lecture_reviews.redis.Redis")
    def test_redis_connection_error_fallback_to_db(self, mock_redis: MagicMock) -> None:
        fake_redis = mock_redis.return_value
        fake_redis.get.side_effect = redis.exceptions.ConnectionError
        fake_redis.set.side_effect = redis.exceptions.ConnectionError

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)  # DB에서 가져온 데이터 확인

    @patch("apps.lectures.views.lecture_reviews.redis.Redis")
    def test_invalid_cached_data_fallback_to_db(self, mock_redis: MagicMock) -> None:
        fake_redis = mock_redis.return_value
        fake_redis.get.return_value = "INVALID_JSON"

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)  # DB에서 가져온 데이터 확인

    def test_empty_reviews(self) -> None:
        LectureReview.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": [], "next": None, "previous": None})
