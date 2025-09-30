import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_search_logs import LectureSearchLog
from apps.lectures.models.user_prefer_categories import UserPreferCategory
from apps.lectures.services.recommend_lecture_service import RecommendLectureService

User = get_user_model()


class RecommendLectureServiceTestCase(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.service = RecommendLectureService()

        # 테스트 유저 생성
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            birthday=date(2000, 1, 1),
        )

        # 카테고리 생성 (UserPreferCategory FK용)
        self.category = Category.objects.create(name="AI")

        # 강의 데이터 생성
        self.lecture1 = Lecture.objects.create(
            uuid=uuid.uuid4(),
            title="파이썬 기초",
            instructor="홍길동",
            average_rating=4.5,
            duration=100,
            difficulty="초급",
            description="파이썬 입문 강의",
            platform="유데미",
            original_price=10000,
            discount_price=5000,
            url_link="http://example.com/lecture/1",
            thumbnail_img_url="http://example.com/img1.jpg",
        )
        self.lecture2 = Lecture.objects.create(
            uuid=uuid.uuid4(),
            title="머신러닝 개론",
            instructor="이순신",
            average_rating=4.8,
            duration=200,
            difficulty="중급",
            description="머신러닝 입문",
            platform="인프런",
            original_price=20000,
            discount_price=15000,
            url_link="http://example.com/lecture/2",
            thumbnail_img_url="http://example.com/img2.jpg",
        )
        self.lecture3 = Lecture.objects.create(
            uuid=uuid.uuid4(),
            title="딥러닝 프로젝트",
            instructor="강감찬",
            average_rating=4.9,
            duration=300,
            difficulty="고급",
            description="딥러닝 실전",
            platform="패스트캠퍼스",
            original_price=30000,
            discount_price=25000,
            url_link="http://example.com/lecture/3",
            thumbnail_img_url="http://example.com/img3.jpg",
        )

    def test_get_recommendations_for_anonymous_user(self) -> None:
        """비로그인 사용자는 단순히 처음 page_size 개 강의를 받는다."""
        request = self.factory.get("/lectures/recommend")
        request.user = AnonymousUser()  # ✅ 익명 유저 처리

        response = self.service.get(request)

        self.assertEqual(response.status_code, 200)
        data = response.data["results"]
        self.assertEqual(len(data), self.service.page_size)
        self.assertEqual(data[0]["title"], self.lecture1.title)

    def test_get_recommendations_with_user_history(self) -> None:
        """로그인 유저의 검색 키워드 기반 추천이 동작하는지 확인"""
        # 검색 기록 저장
        LectureSearchLog.objects.create(user=self.user, keyword="머신러닝")

        # 선호 카테고리 연결
        UserPreferCategory.objects.create(user=self.user, category=self.category)

        wsgi_request = self.factory.get("/lectures/recommend")
        force_authenticate(wsgi_request, user=self.user)
        request = Request(wsgi_request)  # ✅ DRF Request로 변환

        response = self.service.get(request)
        self.assertEqual(response.status_code, 200)
        data = response.data["results"]

        # 머신러닝과 관련된 강의(lecture2)가 추천 결과에 포함되는지 체크
        titles = [lecture["title"] for lecture in data]
        self.assertIn(self.lecture2.title, titles)

    def test_no_lectures_returns_empty_list(self) -> None:
        """강의 데이터가 없으면 빈 리스트를 반환한다."""
        Lecture.objects.all().delete()

        request = self.factory.get("/lectures/recommend")
        request.user = AnonymousUser()  # 익명 유저 처리

        response = self.service.get(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    def test_cbf_algorithm_with_no_lectures_returns_empty(self) -> None:
        """강의 데이터가 없으면 cbf_algorithm이 빈 리스트를 반환하는지 확인"""
        result = self.service.cbf_algorithm(
            search_keywords=["머신러닝"], preferred_categories=["인공지능"], lectures=[]
        )
        self.assertEqual(result, [])
