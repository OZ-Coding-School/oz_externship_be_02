from datetime import date, timedelta
from typing import Any, ClassVar, Dict, Optional

from django.urls import reverse  # 사용자님의 좋은 방식
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models import Application
from apps.applications.serializers.application_detail_serializers import (
    ApplicationDetailSerializer,
)
from apps.recruitments.models import Recruitment
from apps.studies.models import StudyGroup
from apps.users.models import User


class ApplicationDetailAPITest(APITestCase):
    applicant: ClassVar[User]
    author: ClassVar[User]
    other: ClassVar[User]
    study_group: ClassVar[StudyGroup]
    recruitment: ClassVar[Recruitment]
    application: ClassVar[Application]
    url: ClassVar[str]

    @classmethod
    def create_test_user(
        cls,
        email: str,
        nickname: str,
        gender: str = "male",
        birthday: date = date(2002, 3, 14),
        name: str = "홍길동",
        phone_number: Optional[str] = None,
        profile_img_url: str = "https://example.com/profile.jpg",
        password: str = "testpass123",
    ) -> User:
        if phone_number is None:
            count = User.objects.count()
            phone_number = f"010{1000 + count:04d}{1000 + count:04d}"

        return User.objects.create_user(
            email=email,
            nickname=nickname,
            gender=gender,
            birthday=birthday,
            name=name,
            phone_number=phone_number,
            profile_img_url=profile_img_url,
            password=password,
        )

    @staticmethod
    def get_expected_application_data(application: Application) -> Dict[str, Any]:
        return ApplicationDetailSerializer(application).data

    @classmethod
    def setUpTestData(cls) -> None:
        cls.applicant = cls.create_test_user(email="applicant@example.com", nickname="지원자")
        cls.author = cls.create_test_user(email="recruiter@example.com", nickname="작성자")
        cls.other = cls.create_test_user(email="other@example.com", nickname="외부인")

        cls.study_group = StudyGroup.objects.create(
            name="테스트 스터디",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )

        cls.recruitment = Recruitment.objects.create(
            study_group=cls.study_group,  # StudyGroup 객체 필요
            author=cls.author,
            title="테스트 모집글",
            content="테스트 내용",
            estimated_fee=10000,
            expected_headcount=5,
        )

        cls.application = Application.objects.create(
            recruitment=cls.recruitment,
            user=cls.applicant,
            objective="목표",
            motivation="동기",
            self_introduction="자기소개",
            available_time="주말",
            has_study_experience=True,
            study_experience="있음",
            status=Application.ApplicationStatus.PENDING,
        )
        # 사용자님의 좋은 방식
        cls.url = reverse("application-detail", kwargs={"application_id": cls.application.id})

    def test_success_applicant_can_view_own_application(self) -> None:
        """[성공] 지원자 본인은 자신의 지원서를 조회할 수 있습니다."""
        self.client.force_authenticate(user=self.applicant)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 헬퍼 함수를 이용해 응답 전체를 한 번에 비교
        self.assertEqual(response.data, self.get_expected_application_data(self.application))

    def test_success_author_can_view_application(self) -> None:
        """[성공] 공고 작성자는 해당 공고에 달린 지원서를 조회할 수 있습니다."""
        self.client.force_authenticate(user=self.author)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.get_expected_application_data(self.application))

    def test_fail_unauthorized_user_returns_403(self) -> None:
        """[실패] 관계 없는 제3자는 403 Forbidden 에러를 받습니다."""
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_fail_unauthenticated_user_returns_401(self) -> None:
        """[실패] 로그인하지 않은 사용자는 401 Unauthorized 에러를 받습니다."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_nonexistent_application_returns_404(self) -> None:
        """[실패] 존재하지 않는 지원서 ID로 요청하면 404 Not Found 에러를 받습니다."""
        self.client.force_authenticate(user=self.author)
        non_existent_url = reverse("application-detail", kwargs={"application_id": 9999})
        response = self.client.get(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 승인

    def test_success_author_can_approve_pending_application(self) -> None:
        url = reverse("application-approve", kwargs={"application_id": self.application.id})
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.ApplicationStatus.ACCEPTED)
        self.assertIn(self.application.user, self.study_group.members.all())

    def test_fail_author_can_approve_already_appproved(self) -> None:
        self.application.status = Application.ApplicationStatus.ACCEPTED
        self.application.save()

        url = reverse("application-approve", kwargs={"application_id": self.application.id})
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_other_user_cannot_approve(self) -> None:
        url = reverse("application-approve", kwargs={"application_id": self.application.id})
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 거절

    def test_success_author_can_reject_pending_application(self) -> None:
        url = reverse("application-reject", kwargs={"application_id": self.application.id})
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.ApplicationStatus.REJECTED)

    def test_fail_author_cannot_reject_already_rejected(self) -> None:
        self.application.status = Application.ApplicationStatus.REJECTED
        self.application.save()

        url = reverse("application-reject", kwargs={"application_id": self.application.id})
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_other_user_cannot_reject(self) -> None:
        url = reverse("application-reject", kwargs={"application_id": self.application.id})
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
