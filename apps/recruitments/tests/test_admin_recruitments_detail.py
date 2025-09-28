from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models.applications import Application
from apps.lectures.models import Lecture
from apps.recruitments.models import Recruitment, RecruitmentAttachment, Tag
from apps.studies.models import StudyGroup

# 필요한 모델들을 정확한 경로에서 import 합니다.
from apps.users.models import User

CustomUser = get_user_model()


class AdminRecruitmentDetailViewTest(APITestCase):
    """관리자용 구인공고 상세 조회 API 테스트"""

    def setUp(self) -> None:
        # (User, StudyGroup, Lecture, Recruitment, Tag 등 생성 코드는 동일)
        self.admin_user = User.objects.create_superuser(
            email="admin@test.com",
            password="testpassword",
            nickname="admin",
            birthday=date(1990, 1, 1),
        )

        self.regular_user1 = User.objects.create_user(
            "user1@test.com",
            "pw",
            nickname="user1",
            birthday=date(1995, 5, 15),  # ✅ 추가
        )

        self.regular_user2 = User.objects.create_user(
            "user2@test.com",
            "pw",
            nickname="user2",
            birthday=date(1996, 6, 20),  # ✅ 추가
        )
        self.study_group = StudyGroup.objects.create(
            name="테스트 스터디",
            introduction="테스트용 스터디 소개",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=7),
        )
        self.lecture1 = Lecture.objects.create(
            title="강의 1",
            original_price=10000,
            duration=60,
        )
        self.lecture2 = Lecture.objects.create(
            title="강의 2",
            original_price=15000,
            duration=90,
        )
        self.study_group.lectures.add(self.lecture1, self.lecture2)

        self.recruitment = Recruitment.objects.create(
            author=self.admin_user,
            study_group=self.study_group,
            title="테스트 공고",
            content="내용",
            estimated_fee=10000,
            expected_headcount=5,
            close_at=timezone.now() + timedelta(days=7),
        )
        tag1 = Tag.objects.create(name="Python")
        self.recruitment.tags.add(tag1)
        RecruitmentAttachment.objects.create(recruitment=self.recruitment, file_name="자료.pdf", file_url="http://a.b")
        self.recruitment.bookmark_users.add(self.regular_user1, self.regular_user2)

        Application.objects.create(
            recruitment=self.recruitment,
            user=self.regular_user1,
            status=Application.ApplicationStatus.PENDING,
            objective="테스트 목표",
            motivation="테스트 동기",
            self_introduction="테스트 자기소개",
            available_time="월, 수 저녁",
        )

        self.url = reverse("admin-recruitment-detail", kwargs={"recruitment_id": self.recruitment.id})

    def test_get_detail_as_admin_success(self) -> None:
        # 관리자가 상세 조회 시, 200 OK와 함께 모든 데이터가 정확히 반환
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["id"], self.recruitment.id)
        self.assertEqual(len(data["applications"]), 1)
        # Application 모델의 status enum 값은 'PENDING' 이므로, 응답도 'PENDING' 이어야 함
        self.assertEqual(data["applications"][0]["status"], "PENDING")
        self.assertEqual(data["applications"][0]["applicant_nickname"], self.regular_user1.nickname)

    def test_get_detail_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        not_found_url = reverse("admin-recruitment-detail", kwargs={"recruitment_id": 9999})
        response = self.client.get(not_found_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_detail_permission_denied_for_non_admin(self) -> None:
        self.client.force_authenticate(user=self.regular_user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_detail_unauthenticated(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expected_payment_return_discount_sum(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        expected = (self.lecture1.original_price + self.lecture2.original_price) - (
            (self.lecture1.discount_price or 0) + (self.lecture2.discount_price or 0)
        )
        self.assertEqual(data["expected_payment_cost"], expected)
