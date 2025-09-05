from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitments.models.recruitment_attachments import RecruitmentAttachment
from apps.recruitments.models.recruitment_tags import RecruitmentTag
from apps.recruitments.models.recruitments import Recruitment
from apps.recruitments.models.tags import Tag
from apps.studies.models.study_groups import StudyGroup
from apps.users.models.user import User


class RecruitmentDetailViewMockTest(APITestCase):

    def setUp(self) -> None:
        # 테스트 실행 전, API가 조회할 데이터를 미리 DB에 생성
        author = User.objects.create_user(
            email="author@example.com",
            password="password123",
            nickname="해파리볶음밥",
            birthday=date(2002, 3, 14),
            phone_number="010-1111-1111",
        )
        bookmark_user = User.objects.create_user(
            email="bookmark@example.com",
            password="password123",
            birthday=date(2001, 2, 2),
            phone_number="010-2222-2222",
        )

        now = timezone.now()
        study_group = StudyGroup.objects.create(
            name="Mock Study", max_headcount=10, start_at=now, end_at=now + timedelta(days=30)
        )

        self.recruitment = Recruitment.objects.create(
            study_group=study_group,
            author=author,
            title="test",
            content="test",
            expected_headcount=5,
            estimated_fee=25000,
            views_count=100,
        )

        tag = Tag.objects.create(name="#Django")
        RecruitmentTag.objects.create(recruitment=self.recruitment, tag=tag)

        RecruitmentAttachment.objects.create(
            recruitment=self.recruitment,
            file_url="https://example.com/study_plan_mock.pdf",
            file_name="study_plan_mock.pdf",
        )

        self.recruitment.bookmark_users.add(bookmark_user)

    def test_get_recruitment_detail_mock_success(self) -> None:
        # GIVEN
        url = reverse("recruitment-detail", kwargs={"recruitment_id": self.recruitment.id})

        # WHEN
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["id"], self.recruitment.id)
        self.assertIn("author", data)
        self.assertIn("title", data)
        self.assertIn("content", data)
        self.assertIn("attachments", data)
        self.assertIn("expected_headcount", data)
        self.assertIn("estimated_fee", data)
        self.assertIn("study_lectures", data)
        self.assertIn("tags", data)
        self.assertIn("close_at", data)
        self.assertIn("created_at", data)
        self.assertIn("views_count", data)
        self.assertIn("bookmark_count", data)
        self.assertEqual(data["author"]["nickname"], "해파리볶음밥")
