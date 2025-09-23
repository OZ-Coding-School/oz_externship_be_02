import json
import logging
import uuid
from typing import Any, Dict, List, Set, cast
from unittest.mock import MagicMock, patch

import redis
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.lectures.managers.Lecture_manager import LectureQuerySet
from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_categories import LectureCategory
from apps.lectures.serializers.crawled_lecture import LectureSerializer
from apps.lectures.services.lecture_list_service import get_lectures
from apps.lectures.views.lecture_list import LectureListView
from apps.users.models.user import User

logger = logging.getLogger(__name__)


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

    def test_lecture_list_view_get(self) -> None:
        """필터 없이 LectureListView 호출 시 전체 강의 반환 확인"""
        response = self.client.get(self.url)  # Client로 GET 요청

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.json())
        self.assertEqual(len(response.json()["results"]), 2)

        titles = [item["title"] for item in response.json()["results"]]
        self.assertIn(self.lecture1.title, titles)
        self.assertIn(self.lecture2.title, titles)

    @patch("apps.lectures.services.lecture_list_service.cache")
    def test_get_lectures_from_cache(self, mock_cache: MagicMock) -> None:
        """캐시에 데이터가 있으면 캐시 데이터를 반환"""
        fake_data = json.dumps([{"title": "캐시 강의"}])
        mock_cache.get.return_value = fake_data

        result = get_lectures()

        self.assertEqual(result, [{"title": "캐시 강의"}])
        mock_cache.get.assert_called_once_with("lectures:list")

    @patch("apps.lectures.services.lecture_list_service.cache")
    def test_get_lectures_from_cache_invalid_json(self, mock_cache: MagicMock) -> None:
        """캐시 JSON이 잘못된 경우 DB에서 조회 fallback"""
        mock_cache.get.return_value = "INVALID_JSON"

        result = get_lectures()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], self.lecture1.title)

    @patch("apps.lectures.services.lecture_list_service.cache")
    def test_get_lectures_cache_set_error(self, mock_cache: MagicMock) -> None:
        """캐시 set 시 예외 발생 → warning 로그 확인 및 DB fallback"""
        mock_cache.get.return_value = None
        mock_cache.set.side_effect = Exception("Cache set failed")

        with patch("apps.lectures.services.lecture_list_service.logger") as mock_logger:
            result = get_lectures()

            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["title"], self.lecture1.title)

            mock_logger.warning.assert_called_once()
            args, _ = mock_logger.warning.call_args
            self.assertIn("Failed to set lectures in cache", args[0])


class LectureQuerySetManagerTest(LectureTestCase):  # 기존 LectureTestCase 활용
    def test_search_queryset(self) -> None:
        qs = Lecture.objects.search("PyTorch")
        self.assertIn(self.lecture1, qs)
        self.assertNotIn(self.lecture2, qs)

        qs = Lecture.objects.search("코딩 파트너2")
        self.assertIn(self.lecture2, qs)
        self.assertNotIn(self.lecture1, qs)

        qs = Lecture.objects.search("")
        self.assertEqual(qs.count(), 2)  # keyword 없으면 전체 반환

    def test_filter_by_categories_queryset(self) -> None:
        qs = Lecture.objects.filter_by_categories("AI")
        self.assertIn(self.lecture1, qs)
        self.assertNotIn(self.lecture2, qs)

        qs = Lecture.objects.filter_by_categories("데이터 사이언스")
        self.assertIn(self.lecture1, qs)
        self.assertIn(self.lecture2, qs)

        qs = Lecture.objects.filter_by_categories("")
        self.assertEqual(qs.count(), 2)  # 빈 문자열이면 전체 반환

    def test_sort_by_ordering_queryset(self) -> None:
        #
        # price_asc
        qs = Lecture.objects.all().sort_by_ordering("price_asc")  # type: ignore
        self.assertEqual(list(qs), [self.lecture1, self.lecture2])
        # price_desc
        qs = Lecture.objects.all().sort_by_ordering("price_desc")  # type: ignore
        self.assertEqual(list(qs), [self.lecture2, self.lecture1])
        # rating_desc
        qs = Lecture.objects.all().sort_by_ordering("rating_desc")  # type: ignore
        self.assertEqual(list(qs), [self.lecture1, self.lecture2])
        # rating_asc
        qs = Lecture.objects.all().sort_by_ordering("rating_asc")  # type: ignore
        self.assertEqual(list(qs), [self.lecture2, self.lecture1])
        # default
        qs = Lecture.objects.all().sort_by_ordering(None)  # type: ignore
        self.assertEqual(list(qs), [self.lecture2, self.lecture1])
