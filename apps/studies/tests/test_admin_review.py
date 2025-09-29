from datetime import datetime

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse

from django.utils import timezone

from apps.core.tests.mixins.test_user_mixins import TestUserMixin
from apps.studies.models import StudyReview, StudyGroup
from apps.users.models import User


class AdminReviewListViewTest(APITestCase, TestUserMixin):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = cls._create_test_user(
            nickname='admin', email='admin@example.com', password='adminpass', is_staff=True
        )
        cls.user1 = cls._create_test_user(
            nickname='user1', email='user1@example.com', password='userpass1', phone_number = "01012345679",
        )
        cls.user2 = cls._create_test_user(
            nickname='user2', email='user2@example.com', password='userpass2', phone_number = "01012345670",
        )
        cls.study_group = StudyGroup.objects.create(
            name='Test Study Group',
            max_headcount=5,
            start_at=datetime(2025, 9, 15),
            end_at=datetime(2025, 10, 30),
        )

        # 고정 날짜로 안정성 높임 (naive datetime을 aware하게 변환)
        naive_date1 = datetime(2020, 9, 27, 0, 0, 0)  # 오래된 리뷰
        aware_date1 = timezone.make_aware(naive_date1)  # 설정값으로 aware하게 만듦
        cls.review1 = StudyReview.objects.create(
            study_group=cls.study_group, user=cls.user1, content='Great review', star_rating=5,
            created_at=aware_date1
        )

        naive_date2 = datetime(2025, 9, 27, 0, 0, 0)  # 최신 리뷰
        aware_date2 = timezone.make_aware(naive_date2)
        cls.review2 = StudyReview.objects.create(
            study_group=cls.study_group, user=cls.user2, content='Okay review', star_rating=3,
            created_at=aware_date2
        )
        cls.url = reverse('admin-review-list')

    def setUp(self):
        self.client = APIClient()

    def test_admin_user_can_access_review_list(self):
        """관리자 유저가 리뷰 목록을 조회할 수 있는지 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # 페이징된 결과 2개 확인

    def test_non_admin_user_cannot_access(self):
        """비관리자 유저가 접근 불가 (403 Forbidden) 테스트"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_user_nickname(self):
        """사용자 닉네임으로 필터링 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'user_nickname': 'user1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['user_nickname'], 'user1')  # 시리얼라이저 필드 확인

    def test_filter_by_user_email(self):
        """사용자 이메일으로 필터링 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'user_email': 'user2@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['user_email'], 'user2@example.com')

    def test_ordering_oldest_first(self):
        """오래된 순 정렬 (ordering=created_at) 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'ordering': 'created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        # created_at이 오래된 순으로 정렬되었는지 확인 (review1이 먼저)
        self.assertEqual(results[0]['id'], self.review1.id)
        self.assertEqual(results[1]['id'], self.review2.id)

    def test_ordering_latest_first_default(self):
        """기본 정렬 (최신순, -created_at) 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        # created_at이 최신 순으로 정렬되었는지 확인 (review2가 먼저)
        self.assertEqual(results[0]['id'], self.review2.id)
        self.assertEqual(results[1]['id'], self.review1.id)

    def test_invalid_ordering_defaults_to_latest(self):
        """유효하지 않은 ordering 시 기본값 (-created_at) 적용 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'ordering': 'invalid_field'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        # 기본 최신순으로 정렬되었는지 확인
        self.assertEqual(results[0]['id'], self.review2.id)
        self.assertEqual(results[1]['id'], self.review1.id)
