from datetime import datetime, timedelta
from django.utils import timezone

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
    @classmethod
    def setUpTestData(cls) -> None:
        cls.study_group = StudyGroup.objects.create(
            name="test group",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now()+timedelta(days=1),
        )
        cls.lecture1 = Lecture.objects.create(
            title="lecture 1",
            instructor="instructor 1",
            duration=5,
            description="description 1",
            platform="udemy",
            url_link="https://www.test.com",
        )
        cls.lecture2 = Lecture.objects.create(
            title="lecture 2",
            instructor="instructor 2",
            duration=5,
            description="description 2",
            platform="udemy",
            url_link="https://www.test.com",
        )
        StudyLecture.objects.create(lecture=cls.lecture1, study_group=cls.study_group)
        StudyLecture.objects.create(lecture=cls.lecture2, study_group=cls.study_group)

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
        cls.tag1 = Tag.objects.create(name="tag1")
        cls.tag2 = Tag.objects.create(name="tag2")
        cls.tag3 = Tag.objects.create(name="tag3")
        RecruitmentTag.objects.create(tag=cls.tag1, recruitment=cls.recruitment)
        RecruitmentTag.objects.create(tag=cls.tag2, recruitment=cls.recruitment)
        RecruitmentTag.objects.create(tag=cls.tag3, recruitment=cls.recruitment)

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_recruitment_list_get(self) -> None:
        url = reverse("recruitment")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        self.assertEqual(len(res.data),1)
        data=res.data[0]
        #print(data)
        self.assertEqual(len(data["lectures"]),2)
        self.assertEqual(len(data["tags"]),3)