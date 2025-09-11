import uuid
from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.lectures.models.crawled_lectures import Lecture
from apps.recruitments.models.recruitment_attachments import RecruitmentAttachment
from apps.recruitments.models.recruitment_tags import RecruitmentTag
from apps.recruitments.models.recruitments import Recruitment
from apps.recruitments.models.tags import Tag
from apps.recruitments.serializers.recruitments_serializers import (
    RecruitmentDetailSerializer,
)
from apps.studies.models.study_groups import StudyGroup
from apps.users.models.user import User


class RecruitmentDetailViewTest(APITestCase):
    # 스터디 구인 공고 상세 조회 API의 전체 흐름을 테스트

    def setUp(self) -> None:
        self.author = User.objects.create_user(
            email="author@example.com",
            password="password123",
            nickname="해파리볶음밥",
            birthday=date(2002, 3, 14),
            phone_number="010-1111-1111",
        )
        self.other_user = User.objects.create_user(
            email="bookmark@example.com",
            password="password123",
            birthday=date(2001, 2, 2),
            phone_number="010-2222-2222",
        )

        now = timezone.now()
        study_group = StudyGroup.objects.create(
            name="Mock Study", max_headcount=10, start_at=now, end_at=now + timedelta(days=30)
        )

        # Serializer가 필요로 하는 실제 Lecture 데이터를 생성.
        lecture = Lecture.objects.create(
            title="실제 강의 제목",
            instructor="실제 강사 이름",
            duration=180,
            difficulty="easy",
            platform="inflearn",
            url_link="https://example.com/lecture",
            thumbnail_img_url="https://example.com/thumbnail.jpg",
        )
        # 생성한 강의를 스터디 그룹에 연결
        study_group.lectures.add(lecture)

        self.recruitment = Recruitment.objects.create(
            study_group=study_group,
            author=self.author,
            title="API 테스트용 공고",
            content="테스트 내용",
            expected_headcount=5,
            estimated_fee=25000,
            views_count=100,
        )

        tag = Tag.objects.create(name="#Django")
        RecruitmentTag.objects.create(recruitment=self.recruitment, tag=tag)

        RecruitmentAttachment.objects.create(
            recruitment=self.recruitment,
            file_url="https://example.com/study_plan.pdf",
            file_name="study_plan.pdf",
        )

        self.recruitment.bookmark_users.add(self.other_user)

    def test_get_recruitment_detail_success(self) -> None:
        # GIVEN
        url = reverse("recruitment-detail", kwargs={"recruitment_uuid": self.recruitment.uuid})
        expected_data = RecruitmentDetailSerializer(instance=self.recruitment).data
        # WHEN
        response = self.client.get(url)
        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_get_recruitment_detail_not_found(self) -> None:
        # GIVEN
        non_existent_uuid = uuid.uuid4()
        url = reverse("recruitment-detail", kwargs={"recruitment_uuid": non_existent_uuid})
        # WHEN
        response = self.client.get(url)
        # THEN
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_recruitment_success(self) -> None:
        self.client.force_authenticate(user=self.author)
        url = reverse("recruitment-detail", kwargs={"recruitment_uuid": self.recruitment.uuid})
        update_data = {
            "title": "수정된 제목입니다.",
            "tags": ["Python", "NewTag"],
        }

        response = self.client.patch(url, data=update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "수정된 제목입니다.")
        self.assertEqual(len(response.data["tags"]), 2)
        self.assertIn("Python", [tag["name"] for tag in response.data["tags"]])

    def test_update_recruitment_with_attachments_success(self) -> None:
        # GIVEN
        self.client.force_authenticate(user=self.author)
        url = reverse("recruitment-detail", kwargs={"recruitment_uuid": self.recruitment.uuid})
        update_data = {
            "title": "첨부파일 수정 완료",
            "attachments": [
                {"file_name": "new_file_1.pdf", "file_url": "https://example.com/new_file_1.pdf"},
                {"file_name": "new_file_2.pdf", "file_url": "https://example.com/new_file_2.pdf"},
            ],
        }
        # WHEN
        response = self.client.patch(url, data=update_data, format="json")
        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "첨부파일 수정 완료")
        # 응답 데이터에서 첨부파일 2개로 변경됐는지 확인
        self.assertEqual(len(response.data["attachments"]), 2)
        self.assertEqual(response.data["attachments"][0]["file_name"], "new_file_1.pdf")
        self.assertEqual(self.recruitment.attachments.all().count(), 2)

        # 다른 사용자가 수정 시도 시 403 에러

    def test_update_recruitment_permission_denied(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        url = reverse("recruitment-detail", kwargs={"recruitment_uuid": self.recruitment.uuid})
        update_data = {"title": "잘못된 사용자"}

        response = self.client.patch(url, data=update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
