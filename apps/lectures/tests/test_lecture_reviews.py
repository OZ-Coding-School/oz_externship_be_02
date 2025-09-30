import uuid

from django.test import Client, TestCase
from django.urls import reverse

from apps.lectures.models.crawled_lecture_reviews import LectureReview
from apps.lectures.models.crawled_lectures import Lecture


class LectureReviewsViewTestCase(TestCase):
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

        # 리뷰 샘플 생성
        self.review1 = LectureReview.objects.create(
            lecture=self.lecture,
            content="Great lecture!",
            rating="5_OUT_OF_5_STARS",
        )
        self.review2 = LectureReview.objects.create(
            lecture=self.lecture,
            content="Needs improvement",
            rating="4_OUT_OF_5_STARS",
        )

        self.client = Client()
        self.url = reverse("lectures:lecture_reviews", kwargs={"lecture_uuid": self.lecture.uuid})

    def test_get_reviews_success(self) -> None:
        """리뷰가 있으면 정상적으로 반환된다."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["content"], self.review1.content)
        self.assertEqual(results[1]["content"], self.review2.content)

    def test_empty_reviews(self) -> None:
        """리뷰가 없으면 빈 리스트와 next/previous=None이 반환된다."""
        LectureReview.objects.all().delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": [], "next": None, "previous": None})

    def test_invalid_uuid_returns_empty(self) -> None:
        """없는 강의 UUID로 요청하면 빈 리스트가 반환된다."""
        url = reverse("lectures:lecture_reviews", kwargs={"lecture_uuid": uuid.uuid4()})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": [], "next": None, "previous": None})
