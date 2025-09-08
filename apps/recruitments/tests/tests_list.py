import datetime

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.lectures.models.crawled_lectures import Lecture
from apps.recruitments.models.recruitment_tags import RecruitmentTag
from apps.recruitments.models.recruitments import Recruitment
from apps.recruitments.models.tags import Tag
from apps.studies.models.study_groups import StudyGroup
from apps.studies.models.study_lectures import StudyLecture
from apps.users.models.user import User


class RecruitmentsListTestCase(APITestCase):
    def setUp(self) -> None:
        self.study_group = StudyGroup.objects.create(
            name="test group", max_headcount=5, start_at=datetime.date.today(), end_at=datetime.date.today()
        )
        self.lecture1 = Lecture.objects.create(
            title="lecture 1",
            instructor="instructor 1",
            duration=5,
            description="description 1",
            platform="udemy",
            url_link="https://www.test.com",
        )
        self.lecture2 = Lecture.objects.create(
            title="lecture 2",
            instructor="instructor 2",
            duration=5,
            description="description 2",
            platform="udemy",
            url_link="https://www.test.com",
        )
        StudyLecture.objects.create(lecture=self.lecture1, study_group=self.study_group)
        StudyLecture.objects.create(lecture=self.lecture2, study_group=self.study_group)

        self.user = User.objects.create_user(
            email="test@test.com",
            password="itspassword",
            name="test",
            nickname="test",
            phone_number="010-0000-0000",
            gender="male",
            birthday=datetime.date(2000, 1, 1),
        )
        self.client.force_authenticate(user=self.user)

        self.recruitment = Recruitment.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="test recruitment",
            content="test content",
            estimated_fee=50000,
            expected_headcount=5,
        )
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")
        self.tag3 = Tag.objects.create(name="tag3")
        RecruitmentTag.objects.create(tag=self.tag1, recruitment=self.recruitment)
        RecruitmentTag.objects.create(tag=self.tag2, recruitment=self.recruitment)
        RecruitmentTag.objects.create(tag=self.tag3, recruitment=self.recruitment)

    def test_recruitment_list_get(self) -> None:
        url = reverse("recruitment-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        print(res.data)
