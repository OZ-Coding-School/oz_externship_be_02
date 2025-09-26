from datetime import datetime, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.lectures.models.crawled_lectures import Lecture
from apps.recruitments.models.recruitments import Recruitment
from apps.recruitments.models.tags import Tag
from apps.studies.models.study_groups import StudyGroup
from apps.studies.models.study_lectures import StudyLecture
from apps.users.models.user import User


class RecruitmentPostTestCase(APITestCase):
    def setUp(self) -> None:
        study_groups = []
        study_groups.append(
            StudyGroup(
                name="test_group",
                max_headcount=5,
                start_at=timezone.now(),
                end_at=timezone.now() + timedelta(days=1),
            )
        )
        study_groups.append(
            StudyGroup(
                name="test_group_ended",
                max_headcount=5,
                start_at=timezone.now(),
                end_at=timezone.now() + timedelta(days=1),
                status="ENDED",
            )
        )
        self.study_groups = StudyGroup.objects.bulk_create(study_groups)

        lectures = []
        lectures.append(
            Lecture(
                title="lecture 1",
                instructor="instructor 1",
                duration=5,
                description="description 1",
                platform="udemy",
                url_link="https://www.test.com",
                original_price=10000,
            )
        )
        lectures.append(
            Lecture(
                title="lecture 2",
                instructor="instructor 2",
                duration=5,
                description="description 2",
                platform="udemy",
                url_link="https://www.test.com",
                original_price=30000,
            )
        )
        self.lectures = Lecture.objects.bulk_create(lectures)
        study_lectures = [
            StudyLecture(lecture=self.lectures[0], study_group=self.study_groups[0]),
            StudyLecture(lecture=self.lectures[1], study_group=self.study_groups[0]),
        ]
        StudyLecture.objects.bulk_create(study_lectures)

        self.author = User.objects.create_user(
            email=f"testuser@test.com",
            password="itspassword",
            name="test",
            nickname="testuser",
            phone_number=f"010-0000-0000",
            gender="male",
            birthday=timezone.make_aware(datetime(2025, 9, 9)),
        )
        self.client.force_authenticate(user=self.author)

        tags = [Tag(name="tag1"), Tag(name="tag2"), Tag(name="tag3")]
        self.tags = Tag.objects.bulk_create(tags)

    def test_post_recruitment(self) -> None:
        url = reverse("recruitment-list-post")
        data = {
            "title": "자바스크립트 스터디원 모집합니다!",
            "content": "함께 성장할 스터디원을 모집합니다.",
            "close_at": "2025-10-01T23:59:59",
            "expected_headcount": 3,
            "study_group": self.study_groups[0].id,
            "images": ["http://example.com/img1.jpg", "http://example.com/img2.jpg"],
            "attachments": [
                {"file_url": "http://example.com/file1.pdf", "file_name": "file_name_1"},
                {"file_url": "http://example.com/file2.pdf", "file_name": "file_name_2"},
            ],
            "estimated_fee": 10000,
            "tags": [self.tags[0].id, self.tags[2].id],
        }
        res = self.client.post(url, data=data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["title"], data["title"])

    # 결제 비용 자동 합산 확인
    def test_sum_estimated_fee(self) -> None:
        url = reverse("recruitment-list-post")
        data = {
            "title": "결제 비용 자동 합산",
            "content": "함께 성장할 스터디원을 모집합니다.",
            "close_at": "2025-10-01T23:59:59",
            "expected_headcount": 3,
            "study_group": self.study_groups[0].id,
        }
        res = self.client.post(url, data=data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recm = Recruitment.objects.get()
        self.assertEqual(recm.estimated_fee, 40000)

    def test_post_error(self) -> None:
        url = reverse("recruitment-list-post")
        data = {
            "title": "자바스크립트 스터디원 모집합니다!",
            "content": "함께 성장할 스터디원을 모집합니다.",
            "close_at": "2025-10-01T23:59:59",
            "expected_headcount": 3,
            "study_group": self.study_groups[0].id,
            "attachments": [
                {"file_url": "http://example.com/file1.pdf", "file_name": "file_name_1"},
                {"file_url": "http://example.com/file2.pdf", "file_name": "file_name_2"},
                {"file_url": "http://example.com/file3.pdf", "file_name": "file_name_3"},
                {"file_url": "http://example.com/file4.pdf", "file_name": "file_name_4"},
            ],
        }

        res = self.client.post(url, data=data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
