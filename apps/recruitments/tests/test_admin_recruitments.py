from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitments.models import Recruitment, Tag
from apps.studies.models import StudyGroup
from apps.users.models import User


class AdminRecruitmentListViewTest(APITestCase):
    """
    관리자용 구인 공고 목록 조회 API 테스트
    (REQ-RECM-012, REQ-RECM-013)
    """

    admin_user: User
    normal_user: User
    recruitment1: Recruitment
    recruitment2: Recruitment
    recruitment3: Recruitment
    tag_django: Tag
    tag_python: Tag
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        # 1. GIVEN: 유저 생성 (관리자, 일반 사용자)
        cls.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="password",
            is_staff=True,
            name="관리자",
            nickname="admin_nick",
            phone_number="010-0000-0000",
            gender="M",
            birthday=date(1990, 1, 1),
        )
        cls.normal_user = User.objects.create_user(
            email="user@test.com",
            password="password",
            name="일반유저",
            nickname="user_nick",
            phone_number="010-1111-1111",
            gender="F",
            birthday=date(1995, 1, 1),
        )

        # 테스트용 스터디 그룹 생성
        study_group = StudyGroup.objects.create(
            name="테스트 스터디", max_headcount=5, start_at=timezone.now(), end_at=timezone.now() + timedelta(days=30)
        )

        # 테스트용 태그 생성
        cls.tag_django, _ = Tag.objects.get_or_create(name="Django")
        cls.tag_python, _ = Tag.objects.get_or_create(name="Python")

        # 2. GIVEN: 다양한 속성을 가진 공고 데이터 생성
        # 공고 1: 모집중, 조회수 100, 북마크 1개, 태그: Django, Python
        cls.recruitment1 = Recruitment.objects.create(
            author=cls.admin_user,
            study_group=study_group,
            title="[모집중] Django 스터디",
            content="내용1",
            is_closed=False,
            views_count=100,
            created_at=timezone.now() - timedelta(days=2),
            expected_headcount=5,
            estimated_fee=10000,
        )
        cls.recruitment1.tags.add(cls.tag_django, cls.tag_python)
        cls.recruitment1.bookmark_users.add(cls.normal_user)

        # 공고 2: 마감, 조회수 200, 북마크 2개, 태그: Python
        cls.recruitment2 = Recruitment.objects.create(
            author=cls.admin_user,
            study_group=study_group,
            title="[마감] Python 스터디",
            content="내용2",
            is_closed=True,
            views_count=200,
            created_at=timezone.now() - timedelta(days=1),
            expected_headcount=5,
            estimated_fee=10000,
        )
        cls.recruitment2.tags.add(cls.tag_python)
        cls.recruitment2.bookmark_users.add(cls.normal_user, cls.admin_user)

        # 공고 3: 모집중, 조회수 50, 북마크 0개, 태그 없음
        cls.recruitment3 = Recruitment.objects.create(
            author=cls.admin_user,
            study_group=study_group,
            title="[모집중] 알고리즘 스터디",
            content="내용3",
            is_closed=False,
            views_count=50,
            created_at=timezone.now(),
            expected_headcount=5,
            estimated_fee=10000,
        )

        cls.url = reverse("admin-recruitment-list")

    def test_permission_denied_for_anonymous_user(self) -> None:
        """권한 테스트: 비인증 유저 접근 시 401 에러 확인"""
        # WHEN
        response = self.client.get(self.url)
        # THEN
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_denied_for_normal_user(self) -> None:
        """권한 테스트: 일반 유저 접근 시 403 에러 확인"""
        # GIVEN
        self.client.force_authenticate(user=self.normal_user)
        # WHEN
        response = self.client.get(self.url)
        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_list_success_for_admin(self) -> None:
        """기능 테스트: 관리자 기본 목록 조회 성공"""
        # GIVEN
        self.client.force_authenticate(user=self.admin_user)
        # WHEN
        response = self.client.get(self.url)
        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        # 기본 정렬(최신순) 확인
        self.assertEqual(response.data["results"][0]["id"], self.recruitment3.id)

    def test_search_filter(self) -> None:
        """기능 테스트: 제목 검색 기능 확인"""
        # GIVEN
        self.client.force_authenticate(user=self.admin_user)
        # WHEN
        response = self.client.get(self.url, {"search": "Django"})
        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.recruitment1.id)

    def test_status_filter(self) -> None:
        """기능 테스트: 상태 필터링 기능 확인"""
        # GIVEN
        self.client.force_authenticate(user=self.admin_user)
        # WHEN
        response_recruiting = self.client.get(self.url, {"status": "recruiting"})
        response_closed = self.client.get(self.url, {"status": "closed"})
        # THEN
        self.assertEqual(response_recruiting.data["count"], 2)
        self.assertEqual(response_closed.data["count"], 1)
        self.assertEqual(response_closed.data["results"][0]["id"], self.recruitment2.id)

    def test_tags_filter(self) -> None:
        """기능 테스트: 태그 필터링 기능 확인 (단일/다중)"""
        # GIVEN
        self.client.force_authenticate(user=self.admin_user)
        # WHEN: 단일 태그(Django) 필터링
        response_django = self.client.get(self.url, {"tags": self.tag_django.id})
        # THEN
        self.assertEqual(response_django.data["count"], 1)
        self.assertEqual(response_django.data["results"][0]["id"], self.recruitment1.id)

        # WHEN: 단일 태그(Python) 필터링
        response_python = self.client.get(self.url, {"tags": self.tag_python.id})
        # THEN
        self.assertEqual(response_python.data["count"], 2)

        # WHEN: 다중 태그 필터링
        response_multiple = self.client.get(self.url, {"tags": f"{self.tag_django.id},{self.tag_python.id}"})
        # THEN: Django 또는 Python 태그를 가진 공고는 2개
        self.assertEqual(response_multiple.data["count"], 2)

    def test_ordering(self) -> None:
        """기능 테스트: 정렬 기능 확인"""
        # GIVEN
        self.client.force_authenticate(user=self.admin_user)
        # WHEN: 조회수 순 정렬
        response_views = self.client.get(self.url, {"ordering": "-views_count"})
        # THEN
        self.assertEqual(response_views.data["results"][0]["id"], self.recruitment2.id)
        self.assertEqual(response_views.data["results"][1]["id"], self.recruitment1.id)

        # WHEN: 북마크 순 정렬
        response_bookmarks = self.client.get(self.url, {"ordering": "-bookmark_count"})
        # THEN
        self.assertEqual(response_bookmarks.data["results"][0]["id"], self.recruitment2.id)
        self.assertEqual(response_bookmarks.data["results"][1]["id"], self.recruitment1.id)
