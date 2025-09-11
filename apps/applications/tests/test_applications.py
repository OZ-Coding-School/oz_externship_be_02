import uuid
from datetime import datetime

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitments.models import Recruitment
from apps.studies.models import StudyGroup
from apps.users.models import User

from ..models import Application


class ApplicationAPITest(APITestCase):
    def setUp(self) -> None:
        """테스트 케이스 실행 전에 초기 데이터 설정"""
        # ERD를 참고하여 name, phone_number, gender, birthday 등 필수 필드를 추가한다.
        # nickname과 phone_number는 unique 필드이므로 각 유저마다 다른 값을 사용한다.
        self.applicant = User.objects.create_user(
            email="applicant@test.com",
            password="password",
            name="지원자",
            nickname="지원자닉네임",
            phone_number="010-1111-1111",
            gender="M",
            birthday="2000-01-01",
        )
        self.author = User.objects.create_user(
            email="author@test.com",
            password="password",
            name="작성자",
            nickname="작성자닉네임",
            phone_number="010-2222-2222",
            gender="F",
            birthday="1999-01-01",
        )

        # 시간대 정보가 포함된 'aware' datetime 객체를 생성한다.
        aware_start_at = timezone.make_aware(datetime(2025, 1, 1))
        aware_end_at = timezone.make_aware(datetime(2025, 3, 1))

        self.study_group = StudyGroup.objects.create(
            name="테스트 스터디", max_headcount=5, start_at=aware_start_at, end_at=aware_end_at
        )
        self.recruitment = Recruitment.objects.create(
            author=self.author,
            study_group=self.study_group,
            title="테스트 공고",
            content="내용",
            expected_headcount=3,
            estimated_fee=25000,
        )

        self.url = reverse("application-create", kwargs={"recruitment_uuid": self.recruitment.uuid})
        self.valid_payload = {
            "self_introduction": "안녕하세요",
            "motivation": "성장하고 싶습니다",
            "objective": "프로젝트 완수",
            "available_time": "주중 저녁",
            "has_study_experience": False,
        }

    def test_create_application_success(self) -> None:
        """스터디 참여 신청 성공 테스트"""
        self.client.force_authenticate(user=self.applicant)
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Application.objects.filter(user=self.applicant, recruitment=self.recruitment).exists())
        self.assertIn("application_id", response.data)

    def test_create_application_unauthenticated_fails(self) -> None:
        """미인증 사용자 참여 신청 실패 테스트"""
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_duplicate_application_fails(self) -> None:
        """중복 지원 실패 테스트"""
        # 먼저 한 번 지원
        Application.objects.create(user=self.applicant, recruitment=self.recruitment, **self.valid_payload)

        # 다시 지원 시도
        self.client.force_authenticate(user=self.applicant)
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_code"], "DUPLICATE_APPLICATION")

    def test_create_application_for_non_existent_recruitment_fails(self) -> None:
        """존재하지 않는 공고에 지원 실패 테스트"""
        invalid_url = reverse("application-create", kwargs={"recruitment_uuid": uuid.uuid4()})
        self.client.force_authenticate(user=self.applicant)
        response = self.client.post(invalid_url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_conditional_validation_fails(self) -> None:
        """'스터디 경험' 필드 조건부 유효성 검사 실패 테스트"""
        payload = self.valid_payload.copy()
        payload["has_study_experience"] = True
        # study_experience 필드를 보내지 않음

        self.client.force_authenticate(user=self.applicant)
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("study_experience", response.data["message"])
