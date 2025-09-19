from datetime import datetime, timedelta
from typing import Dict, Final, Union

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
    study_groups: list[StudyGroup]
    lectures: list[Lecture]
    recruitments: list[Recruitment]
    tags: list[Tag]
    users: list[User]
    recruitment_bookmarks: list[RecruitmentBookmark]

    @classmethod
    def setUpTestData(cls) -> None:
        study_groups = []
        study_groups.append(
            StudyGroup(
                name="test group1",
                max_headcount=5,
                start_at=timezone.now(),
                end_at=timezone.now() + timedelta(days=1),
            )
        )
        study_groups.append(
            StudyGroup(
                name="test group2",
                max_headcount=5,
                start_at=timezone.now(),
                end_at=timezone.now() + timedelta(days=1),
            )
        )
        cls.study_groups = StudyGroup.objects.bulk_create(study_groups)

        lectures = []
        lectures.append(
            Lecture(
                title="lecture 1",
                instructor="instructor 1",
                duration=5,
                description="description 1",
                platform="udemy",
                url_link="https://www.test.com",
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
            )
        )
        lectures.append(
            Lecture(
                title="lecture 3",
                instructor="instructor 3",
                duration=5,
                description="description 3",
                platform="udemy",
                url_link="https://www.test.com",
            )
        )
        cls.lectures = Lecture.objects.bulk_create(lectures)

        study_lectures = [
            StudyLecture(lecture=cls.lectures[0], study_group=cls.study_groups[0]),
            StudyLecture(lecture=cls.lectures[1], study_group=cls.study_groups[0]),
            StudyLecture(lecture=cls.lectures[2], study_group=cls.study_groups[1]),
        ]
        StudyLecture.objects.bulk_create(study_lectures)

        users = []
        for i in range(5):
            users.append(
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
        cls.users = User.objects.bulk_create(users)

        RECRUITMENT_CASE_1: Final = 10
        RECRUITMENT_CASE_2: Final = 5
        recruitments = []
        for i in range(RECRUITMENT_CASE_1):
            recruitments.append(
                Recruitment(
                    study_group=cls.study_groups[0],
                    author=cls.users[0],
                    title=f"test recruitment{i+1}",
                    content="test content",
                    estimated_fee=50000,
                    expected_headcount=5,
                    views_count=RECRUITMENT_CASE_1,
                )
            )
        for i in range(RECRUITMENT_CASE_2):
            recruitments.append(
                Recruitment(
                    study_group=cls.study_groups[1],
                    author=cls.users[1],
                    title=f"test recruitment{i + RECRUITMENT_CASE_1 +1}",
                    content="test content",
                    estimated_fee=50000,
                    expected_headcount=5,
                )
            )
        Recruitment.objects.bulk_create(recruitments)
        Recruitment.objects.filter(title=f"test recruitment{RECRUITMENT_CASE_1 + 1}").update(is_closed=True)
        cls.recruitments= Recruitment.objects.all()

        tags = [Tag(name="tag1"), Tag(name="tag2"), Tag(name="tag3"), Tag(name="tag4")]
        cls.tags = Tag.objects.bulk_create(tags)

        recruitment_tags = []
        for i in range(RECRUITMENT_CASE_1):
            for j in range(3):
                recruitment_tags.append(RecruitmentTag(tag=cls.tags[j], recruitment=cls.recruitments[i]))

        for i in range(RECRUITMENT_CASE_2):
            recruitment_tags.append(
                RecruitmentTag(tag=cls.tags[3], recruitment=cls.recruitments[i + RECRUITMENT_CASE_1])
            )
        RecruitmentTag.objects.bulk_create(recruitment_tags)

        recruitment_bookmarks = []
        for i in range(5):
            for j in range(5 - i):
                recruitment_bookmarks.append(
                    RecruitmentBookmark(recruitment=cls.recruitments[i + 5], user=cls.users[j])
                )
        RecruitmentBookmark.objects.bulk_create(recruitment_bookmarks)

    def setUp(self):
        self.client.force_authenticate(user=self.users[1])

    def test_list_get(self) -> None:
        url = reverse("recruitment-list")
        query_params = {"page": 1, 'ordering':'created_at'}
        res = self.client.get(url, query_params)
        self.assertEqual(res.status_code, 200)
        results = res.data["results"]
        data = results[0]  # case1
        self.assertEqual(len(data["lectures"]), 2)
        self.assertEqual(len(data["tags"]), 3)

    def test_list_page(self) -> None:
        url = reverse("recruitment-list")
        query_params = {"page": 1, "size": 3}
        res = self.client.get(url, query_params)
        self.assertEqual(res.status_code, 200)
        results = res.data["results"]
        self.assertEqual(len(results), 3)

    def test_list_search(self) -> None:
        url = reverse("recruitment-list")
        query_params: Dict[str, Union[str, int]] = {"page": 1, "search": "3"}
        res = self.client.get(url, query_params)
        self.assertEqual(res.status_code, 200)
        results = res.data["results"]
        self.assertEqual(len(results), 2)

    def test_list_order(self) -> None:
        url = reverse("recruitment-list")
        query_params: Dict[str, Union[str, int]] = {"page": 1, "size": 20, "ordering": "-bookmarks_count,-created_at"}
        res = self.client.get(url, query_params)
        self.assertEqual(res.status_code, 200)
        results = res.data["results"]
        self.assertEqual(results[0]["bookmarks_count"], 5)
        self.assertEqual(results[2]["bookmarks_count"], 3)

    def test_list_filter(self) -> None:
        url = reverse("recruitment-list")
        query_params: Dict[str, Union[str, int]] = {"page": 1, "tag": "tag1"}
        res = self.client.get(url, query_params)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 10)

        query_params = {"page": 1, "tag": "tag4"}
        res = self.client.get(url, query_params)
        self.assertEqual(res.data["count"], 4) # 5개 중 하나는 마감되어서 4개

        query_params = {"page": 1, "tag": "없는 태그"}
        res = self.client.get(url, query_params)
        self.assertEqual(res.data["count"], 0)

    def test_my_list_get(self) -> None:
        url = reverse("recruitment-mylist")
        query_params = {"page": 1}
        # 조회
        res = self.client.get(url, data=query_params)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 5)

        # 필터링
        query_params = {"page": 1, "is_closed": False}
        res = self.client.get(url, data=query_params)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 4)

        query_params = {"page": 1, "is_closed": True}
        res = self.client.get(url, data=query_params)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
