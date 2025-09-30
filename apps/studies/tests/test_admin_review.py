from datetime import datetime

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.tests.mixins.test_user_mixins import TestUserMixin
from apps.studies.models import StudyGroup, StudyReview
from apps.users.models import User


class AdminReviewListViewTest(APITestCase, TestUserMixin):

    url: str
    admin_user: User
    user: User
    user2: User
    study_group: StudyGroup
    review1: StudyReview
    review2: StudyReview
    client: APIClient

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = cls._create_test_user(
            nickname="admin", email="admin@example.com", password="adminpass", is_staff=True
        )
        cls.user = cls._create_test_user(
            nickname="user",
            email="user@example.com",
            password="userpass1",
            phone_number="01012345679",
        )
        cls.user2 = cls._create_test_user(
            nickname="user2",
            email="user2@example.com",
            password="userpass2",
            phone_number="01012345670",
        )
        cls.study_group = StudyGroup.objects.create(
            name="Test Study Group",
            max_headcount=5,
            start_at=datetime(2025, 9, 15),
            end_at=datetime(2025, 10, 30),
        )

        # 고정 날짜로 안정성 높임 (naive datetime을 aware하게 변환)
        naive_date1 = datetime(2020, 9, 27, 0, 0, 0)  # 오래된 리뷰
        aware_date1 = timezone.make_aware(naive_date1)  # 설정값으로 aware하게 만듦
        cls.review1 = StudyReview.objects.create(
            study_group=cls.study_group, user=cls.user, content="Great review", star_rating=5, created_at=aware_date1
        )

        naive_date2 = datetime(2025, 9, 27, 0, 0, 0)  # 최신 리뷰
        aware_date2 = timezone.make_aware(naive_date2)
        cls.review2 = StudyReview.objects.create(
            study_group=cls.study_group, user=cls.user2, content="Okay review", star_rating=3, created_at=aware_date2
        )
        cls.url = reverse("admin-review-list")

    def setUp(self) -> None:
        self.client = APIClient()

    def test_admin_user_can_access_review_list(self) -> None:
        """관리자 유저가 리뷰 목록을 조회할 수 있는지 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # 페이징된 결과 2개 확인

    def test_non_admin_user_cannot_access(self) -> None:
        """비관리자 유저가 접근 불가 (403 Forbidden) 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_user_nickname(self) -> None:
        """사용자 닉네임으로 필터링 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {"user_nickname": "user"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["user_info"]["nickname"], "user")  # 시리얼라이저 필드 확인

    def test_filter_by_user_email(self) -> None:
        """사용자 이메일으로 필터링 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {"user_email": "user2@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["user_info"]["email"], "user2@example.com")

    def test_ordering_oldest_first(self) -> None:
        """오래된 순 정렬 (ordering=created_at) 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {"ordering": "created_at"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        # created_at이 오래된 순으로 정렬되었는지 확인 (review1이 먼저)
        self.assertEqual(results[0]["id"], self.review1.id)
        self.assertEqual(results[1]["id"], self.review2.id)

    def test_ordering_latest_first_default(self) -> None:
        """기본 정렬 (최신순, -created_at) 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        # created_at이 최신 순으로 정렬되었는지 확인 (review2가 먼저)
        self.assertEqual(results[0]["id"], self.review2.id)
        self.assertEqual(results[1]["id"], self.review1.id)

    def test_invalid_ordering_defaults_to_latest(self) -> None:
        """유효하지 않은 ordering 시 기본값 (-created_at) 적용 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {"ordering": "invalid_field"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        # 기본 최신순으로 정렬되었는지 확인
        self.assertEqual(results[0]["id"], self.review2.id)
        self.assertEqual(results[1]["id"], self.review1.id)


class AdminReviewDetailViewTest(APITestCase, TestUserMixin):

    url: str
    admin_user: User
    user: User
    study_group: StudyGroup
    review: StudyReview
    client: APIClient

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = cls._create_test_user(
            nickname="admin", email="admin@example.com", password="adminpass", is_staff=True
        )
        cls.user = cls._create_test_user(
            nickname="user",
            email="user@example.com",
            password="userpass",
            phone_number="01012345679",
        )
        cls.study_group = StudyGroup.objects.create(
            name="Test Study Group",
            max_headcount=5,
            start_at=datetime(2025, 9, 15, 0, 0, 0),
            end_at=datetime(2025, 10, 30, 0, 0, 0),
            introduction="Test study introduction",  # 스터디 소개 (모델에 따라 조정)
        )

        # 고정 날짜로 안정성 높임 (naive datetime을 aware하게 변환)
        naive_date = datetime(2025, 9, 27, 0, 0, 0)
        aware_date = timezone.make_aware(naive_date)
        cls.review = StudyReview.objects.create(
            study_group=cls.study_group, user=cls.user, content="Great review", star_rating=5, created_at=aware_date
        )
        cls.url = reverse("admin-review-detail", kwargs={"pk": cls.review.pk})

    def setUp(self) -> None:
        self.client = APIClient()

    def test_admin_user_can_retrieve_review(self) -> None:
        """관리자 유저가 리뷰 상세 조회 가능한지 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["id"], self.review.id)
        self.assertEqual(data["user_info"]["nickname"], self.user.nickname)
        self.assertEqual(data["user_info"]["email"], self.user.email)
        self.assertEqual(data["content"], self.review.content)
        self.assertEqual(data["star_rating"], self.review.star_rating)
        self.assertEqual(data["study_group_info"]["name"], self.study_group.name)
        start_at_aware = timezone.make_aware(self.study_group.start_at)  # naive to aware (TIME_ZONE 적용)
        end_at_aware = timezone.make_aware(self.study_group.end_at)
        self.assertEqual(
            data["study_group_info"]["start_at"], timezone.localtime(start_at_aware).isoformat()
        )  # '2025-09-15T00:00:00+09:00'
        self.assertEqual(data["study_group_info"]["end_at"], timezone.localtime(end_at_aware).isoformat())
        self.assertEqual(data["study_group_info"]["introduction"], self.study_group.introduction)
        self.assertEqual(data["created_at"], timezone.localtime(self.review.created_at).isoformat())
        self.assertEqual(data["updated_at"], timezone.localtime(self.review.updated_at).isoformat())

    def test_non_admin_user_cannot_retrieve(self) -> None:
        """비관리자 유저가 접근 불가 (403 Forbidden) 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_retrieve(self) -> None:
        """미인증 유저가 접근 불가 (401 Unauthorized) 테스트"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_not_found(self) -> None:
        """존재하지 않는 리뷰 ID로 조회 시 404 Not Found 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        url_not_exist = reverse("admin-review-detail", kwargs={"pk": 999999})  # 존재하지 않는 PK
        response = self.client.get(url_not_exist)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
