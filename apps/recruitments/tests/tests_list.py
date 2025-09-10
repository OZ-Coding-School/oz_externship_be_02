from datetime import datetime, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.lectures.models.crawled_lectures import Lecture
from apps.recruitments.models.recruitment_tags import RecruitmentTag
from apps.recruitments.models.recruitments import Recruitment
from apps.recruitments.models.tags import Tag
from apps.studies.models.study_groups import StudyGroup
from apps.studies.models.study_lectures import StudyLecture
from apps.users.models.user import User


class RecruitmentsListTestCase(APITestCase):
    # setUp과 달리 cls.study_group을 동적으로 속성을 추가하는 것으로 봐서 선언되어있지 않다고 mypy오류가 뜸
    # 클래스에 속성이 존재할 것을 선언하고 타입 명시
    study_group: StudyGroup
    lecture: list[Lecture]
    recruitment: Recruitment
    tag: list[Tag]
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.study_group = StudyGroup.objects.create(
            name="test group",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=1),
        )
        lecture = []
        lecture.append(
            Lecture(
                title="lecture 1",
                instructor="instructor 1",
                duration=5,
                description="description 1",
                platform="udemy",
                url_link="https://www.test.com",
            )
        )
        lecture.append(
            Lecture(
                title="lecture 2",
                instructor="instructor 2",
                duration=5,
                description="description 2",
                platform="udemy",
                url_link="https://www.test.com",
            )
        )
        cls.lecture = Lecture.objects.bulk_create(lecture)
        study_lecture = [
            StudyLecture(lecture=cls.lecture[0], study_group=cls.study_group),
            StudyLecture(lecture=cls.lecture[1], study_group=cls.study_group),
        ]
        StudyLecture.objects.bulk_create(study_lecture)

        cls.user = User.objects.create_user(
            email="test@test.com",
            password="itspassword",
            name="test",
            nickname="test",
            phone_number="010-0000-0000",
            gender="male",
            birthday=timezone.make_aware(datetime(2025, 9, 9)),
        )

        cls.recruitment = Recruitment.objects.create(
            study_group=cls.study_group,
            author=cls.user,
            title="test recruitment",
            content="test content",
            estimated_fee=50000,
            expected_headcount=5,
        )
        tag = [Tag(name="tag1"), Tag(name="tag2"), Tag(name="tag3")]
        cls.tag = Tag.objects.bulk_create(tag)
        recruitment_tag = [
            RecruitmentTag(tag=cls.tag[0], recruitment=cls.recruitment),
            RecruitmentTag(tag=cls.tag[1], recruitment=cls.recruitment),
            RecruitmentTag(tag=cls.tag[2], recruitment=cls.recruitment),
        ]
        RecruitmentTag.objects.bulk_create(recruitment_tag)

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_recruitment_list_get(self) -> None:
        url = reverse("recruitment-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        self.assertEqual(len(res.data), 1)
        data = res.data[0]
        # print(data)
        self.assertEqual(len(data["lectures"]), 2)
        self.assertEqual(len(data["tags"]), 3)
