import json
import uuid
from typing import cast, Dict, Set
from unittest.mock import patch

import fakeredis
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_categories import LectureCategory
from apps.lectures.serializers.crawled_lecture import LectureSerializer
from apps.users.models.user import User


# 테스트 환경에서 LocMemCache 사용
@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class LectureTestCase(TestCase):
    def setUp(self) -> None:
        # Given
        cache.clear()
        self.client = Client()
        self.list_url = reverse("lectures:lecture_list")

        self.category_ai = Category.objects.create(name="AI")
        self.category_web = Category.objects.create(name="웹 개발")
        self.category_ds = Category.objects.create(name="데이터 사이언스")

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

        LectureCategory.objects.create(lecture=self.lecture1, category=self.category_ai)
        LectureCategory.objects.create(lecture=self.lecture1, category=self.category_ds)
        LectureCategory.objects.create(lecture=self.lecture2, category=self.category_ds)
        LectureCategory.objects.create(lecture=self.lecture2, category=self.category_web)

    def prepare_data_for_redis(self) -> None:
        # Given
        lectures = Lecture.objects.all().order_by("-updated_at")
        data_to_cache = []
        for lecture in lectures:
            categories = [{"name": lc.category.name} for lc in lecture.lecturecategory_set.all()]
            data_to_cache.append(
                {
                    "id": lecture.id,
                    "title": lecture.title,
                    "instructor": lecture.instructor,
                    "average_rating": float(lecture.average_rating),
                    "original_price": lecture.original_price,
                    "categories": categories,
                }
            )
        cache.set("lectures:list", json.dumps(data_to_cache), timeout=600)

    def test_lecture_list_from_redis(self) -> None:

        self.prepare_data_for_redis()
        cached_data = cache.get("lectures:list")
        self.assertIsNotNone(cached_data)
        results = json.loads(cached_data)
        self.assertEqual(len(results), 2)
        titles = [r["title"] for r in results]
        self.assertIn(self.lecture1.title, titles)
        self.assertIn(self.lecture2.title, titles)

        for r in results:
            if r["title"] == self.lecture1.title:
                self.assertEqual(r["instructor"], self.lecture1.instructor)
            if r["title"] == self.lecture2.title:
                self.assertEqual(r["instructor"], self.lecture2.instructor)

    def test_search_by_instructor_in_redis(self) -> None:
        # When
        self.prepare_data_for_redis()
        cached_data = json.loads(cache.get("lectures:list"))
        filtered = [l for l in cached_data if "이코딩" in l["instructor"]]
        # Then
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["title"], self.lecture1.title)

    def test_ordering_by_updated_at(self) -> None:
        # When
        self.prepare_data_for_redis()
        cached_data = json.loads(cache.get("lectures:list"))
        sorted_by_updated = sorted(cached_data, key=lambda x: x["id"], reverse=True)
        # Then
        self.assertEqual(sorted_by_updated[0]["title"], self.lecture2.title)
        self.assertEqual(sorted_by_updated[1]["title"], self.lecture1.title)

    def test_ordering_by_price(self) -> None:
        # When
        self.prepare_data_for_redis()
        cached_data = json.loads(cache.get("lectures:list"))
        sorted_by_price = sorted(cached_data, key=lambda x: x["original_price"], reverse=True)
        # Then
        self.assertEqual(sorted_by_price[0]["title"], self.lecture2.title)
        self.assertEqual(sorted_by_price[1]["title"], self.lecture1.title)

    def test_ordering_by_rating(self) -> None:
        # When
        self.prepare_data_for_redis()
        cached_data = json.loads(cache.get("lectures:list"))
        sorted_by_rating = sorted(cached_data, key=lambda x: x["average_rating"], reverse=True)
        # Then
        self.assertEqual(sorted_by_rating[0]["title"], self.lecture1.title)
        self.assertEqual(sorted_by_rating[1]["title"], self.lecture2.title)

    def test_lecture_to_categories(self) -> None:
        # When
        self.prepare_data_for_redis()
        cached_data = json.loads(cache.get("lectures:list"))
        mapping = {l["title"]: {c["name"] for c in l["categories"]} for l in cached_data}
        # Then
        self.assertSetEqual(mapping[self.lecture1.title], {"AI", "데이터 사이언스"})
        self.assertSetEqual(mapping[self.lecture2.title], {"웹 개발", "데이터 사이언스"})

    def test_category_to_lectures(self) -> None:
        # When
        self.prepare_data_for_redis()
        cached_data = json.loads(cache.get("lectures:list"))
        category_map : Dict[str, Set[str]] = {}
        for l in cached_data:
            for c in l["categories"]:
                category_map.setdefault(c["name"], set()).add(l["title"])
        # Then
        self.assertSetEqual(category_map["AI"], {self.lecture1.title})
        self.assertSetEqual(category_map["데이터 사이언스"], {self.lecture1.title, self.lecture2.title})
        self.assertSetEqual(category_map["웹 개발"], {self.lecture2.title})
