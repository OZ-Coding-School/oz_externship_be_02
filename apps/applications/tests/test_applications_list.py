import uuid
from datetime import datetime

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models import Application
from apps.recruitments.models import Recruitment
from apps.studies.models import StudyGroup
from apps.users.models import User


class RecruitmentApplicationListTest(APITestCase):
    """
    REQ-APLY-002: 본인이 작성한 공고에 대한 지원 목록 조회 API 테스트
    """

    def setUp(self) -> None:
        """테스트 케이스 실행 전에 초기 데이터 설정"""
        self.author = User.objects.create_user(
            email="author@test.com",
            password="password",
            name="작성자",
            nickname="a",  # 1 character
            phone_number="010-0000-0000",
            gender="M",
            birthday="1990-01-01",
        )
        self.applicant1 = User.objects.create_user(
            email="applicant1@test.com",
            password="password",
            name="지원자1",
            nickname="app1_nick",  # 9 characters
            phone_number="010-1111-1111",
            gender="F",
            birthday="1995-01-01",
        )
        self.applicant2 = User.objects.create_user(
            email="applicant2@test.com",
            password="password",
            name="지원자2",
            nickname="app2_nick",  # 9 characters
            phone_number="010-2222-2222",
            gender="M",
            birthday="1996-01-01",
        )
        self.other_user = User.objects.create_user(
            email="other@test.com",
            password="password",
            name="다른유저",
            nickname="other_nick",  # 10 characters
            phone_number="010-3333-3333",
            gender="F",
            birthday="1997-01-01",
        )

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

        # 지원서 데이터 생성
        self.application1 = Application.objects.create(
            recruitment=self.recruitment,
            user=self.applicant1,
            objective="목표1",
            motivation="동기1",
            self_introduction="소개1",
            available_time="시간1",
        )
        self.application2 = Application.objects.create(
            recruitment=self.recruitment,
            user=self.applicant2,
            objective="목표2",
            motivation="동기2",
            self_introduction="소개2",
            available_time="시간2",
        )

        self.url = reverse("recruitment-applications", kwargs={"recruitment_uuid": self.recruitment.uuid})

    def test_list_applications_success_as_author(self) -> None:
        """성공: 공고 작성자가 지원자 목록을 조회"""
        self.client.force_authenticate(user=self.author)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # 응답 데이터에 application_id가 포함되어 있는지, 그리고 그 값이 올바른지 확인
        self.assertIn("application_id", response.data["results"][0])
        self.assertEqual(response.data["results"][0]["application_id"], self.application2.id)

        # 최신순으로 반환되는지 확인 (application2가 나중에 생성됨)
        self.assertEqual(response.data["results"][0]["applicant"]["nickname"], "app2_nick")
        self.assertEqual(response.data["results"][1]["applicant"]["nickname"], "app1_nick")

    def test_list_applications_fails_as_applicant(self) -> None:
        """실패: 지원자가 지원자 목록 조회 시도"""
        self.client.force_authenticate(user=self.applicant1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_applications_fails_as_other_user(self) -> None:
        """실패: 관련 없는 다른 유저가 지원자 목록 조회 시도"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_applications_fails_unauthenticated(self) -> None:
        """실패: 미인증 사용자가 지원자 목록 조회 시도"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_applications_for_non_existent_recruitment(self) -> None:
        """실패: 존재하지 않는 공고의 지원자 목록 조회 시도"""
        invalid_url = reverse("recruitment-applications", kwargs={"recruitment_uuid": uuid.uuid4()})
        self.client.force_authenticate(user=self.author)
        response = self.client.get(invalid_url)
        # IsRecruitmentAuthor 권한 클래스에 의해 403 반환
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_applications_pagination(self) -> None:
        """성공: 페이지네이션 동작 확인"""
        # 10명의 지원자 추가 생성
        for i in range(10):
            user = User.objects.create_user(
                email=f"applicant_extra_{i}@test.com",
                password="password",
                name=f"지원자{i+3}",
                nickname=f"app_ext_{i}",
                phone_number=f"010-4444-{i:04d}",
                gender="M",
                birthday="2000-01-01",
            )
            Application.objects.create(
                recruitment=self.recruitment,
                user=user,
                objective=f"목표{i+3}",
                motivation=f"동기{i+3}",
                self_introduction=f"소개{i+3}",
                available_time=f"시간{i+3}",
            )

        self.client.force_authenticate(user=self.author)
        # 페이지 크기를 5로 설정하여 요청
        response = self.client.get(self.url, {"limit": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next_cursor"])

        # 다음 페이지 요청
        next_cursor = response.data["next_cursor"]
        response2 = self.client.get(next_cursor)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data["results"]), 5)
