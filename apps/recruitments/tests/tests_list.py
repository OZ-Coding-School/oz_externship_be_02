from datetime import datetime, timedelta
from typing import Dict, Union

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.lectures.models.crawled_lectures import Lecture
from apps.recruitments.models import RecruitmentBookmark
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
    recruitment: list[Recruitment]
    tag: list[Tag]
    user: list[User]
    recruitment_bookmarks: list[RecruitmentBookmark]

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

        user = []
        for i in range(5):
            user.append(
                User(
                    email=f"testuser{i}@test.com",
                    password="itspassword",
                    name="test",
                    nickname=f"testuser{i}",
                    phone_number=f"010-0000-000{i}",
                    gender="male",
                    birthday=timezone.make_aware(datetime(2025, 9, 9)),
                )
            )
        cls.user = User.objects.bulk_create(user)

        recruitment = []
        for i in range(15):
            recruitment.append(
                Recruitment(
                    study_group=cls.study_group,
                    author=cls.user[0],
                    title=f"test recruitment{i+1}",
                    content="test content",
                    estimated_fee=50000,
                    expected_headcount=5,
                    views_count=15 - i,
                )
            )
        cls.recruitment = Recruitment.objects.bulk_create(recruitment)

        tag = [Tag(name="tag1"), Tag(name="tag2"), Tag(name="tag3")]
        cls.tag = Tag.objects.bulk_create(tag)
        recruitment_tag = []
        for i in range(15):
            for j in range(3):
                recruitment_tag.append(RecruitmentTag(tag=cls.tag[j], recruitment=cls.recruitment[i]))
        RecruitmentTag.objects.bulk_create(recruitment_tag)

        recruitment_bookmarks = []
        for i in range(5):
            for j in range(5 - i):
                recruitment_bookmarks.append(RecruitmentBookmark(recruitment=cls.recruitment[i + 5], user=cls.user[j]))
        RecruitmentBookmark.objects.bulk_create(recruitment_bookmarks)

    def test_list_get(self) -> None:
        url = reverse("recruitment-list")
        query_params = {"page": 1}
        res = self.client.get(url, query_params)
        self.assertEqual(res.status_code, 200)
        results = res.data["results"]
        # for i in results:
        #     print(i['id'])
        data = results[0]
        self.assertEqual(len(data["lectures"]), 2)
        self.assertEqual(len(data["tags"]), 3)

    def test_list_page(self) -> None:
        url = reverse("recruitment-list")
        query_params = {"page": 1, "size": 3}
        res = self.client.get(url, data=query_params)
        self.assertEqual(res.status_code, 200)
        # print(res.data)
        results = res.data["results"]
        self.assertEqual(len(results), 3)

    def test_list_search(self) -> None:
        url = reverse("recruitment-list")
        query_params: Dict[str, Union[str, int]] = {"page": 1, "search": "3"}
        res = self.client.get(url, data=query_params)
        self.assertEqual(res.status_code, 200)
        # print(res.data)
        results = res.data["results"]
        # print(results)
        self.assertEqual(len(results), 2)

    def test_list_order(self) -> None:
        url = reverse("recruitment-list")
        query_params: Dict[str, Union[str, int]] = {"page": 1, "size": 20, "ordering": "-bookmarks_count,-created_at"}
        res = self.client.get(url, data=query_params)
        self.assertEqual(res.status_code, 200)
        results = res.data["results"]
        # for i in results:
        #     print(i["id"], i["bookmarks_count"])