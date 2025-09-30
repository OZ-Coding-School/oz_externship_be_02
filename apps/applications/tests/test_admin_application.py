from datetime import datetime, timedelta
from typing import Dict, Final, Union, cast

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.applications.models.applications import Application
from apps.recruitments.models.recruitments import Recruitment
from apps.studies.models.study_groups import StudyGroup
from apps.users.models.user import User


class AdminApplicationTestCase(APITestCase):
    USER_COUNT: Final = 10
    RECRUITMENT_COUNT: Final = 2
    APPLICATION_COUNT: Final = USER_COUNT * RECRUITMENT_COUNT

    users: list[User]
    recruitments: list[Recruitment]
    study_group: StudyGroup
    applications: list[Application]
    status = [
        Application.ApplicationStatus.PENDING,
        Application.ApplicationStatus.CANCELED,
        Application.ApplicationStatus.ACCEPTED,
        Application.ApplicationStatus.REJECTED,
    ]

    @classmethod
    def setUpTestData(cls) -> None:
        users = []
        for i in range(cls.USER_COUNT - 1):
            users.append(
                User(
                    email=f"testuser{i}@test.com",
                    password="itspassword",
                    name="test",
                    nickname=f"testuser{i}",
                    phone_number=f"010-0000-{i:04d}",
                    gender="male",
                    birthday=timezone.make_aware(datetime(2025, 9, 9)),
                )
            )
        users.append(
            User(
                email="superuser@test.com",
                password="itspassword",
                name="test",
                nickname="superuser",
                phone_number=f"010-0000-{cls.USER_COUNT - 1:04d}",
                gender="male",
                birthday=timezone.make_aware(datetime(2025, 9, 9)),
                is_superuser=True,
            )
        )
        cls.users = User.objects.bulk_create(users)

        cls.study_group = StudyGroup.objects.create(
            name="test group", max_headcount=5, start_at=timezone.now(), end_at=timezone.now() + timedelta(days=1)
        )

        recruitments = []
        for i in range(cls.RECRUITMENT_COUNT):
            recruitments.append(
                Recruitment(
                    study_group=cls.study_group,
                    author=cls.users[0],
                    title=f"test recruitment{i+1}",
                    content="test content",
                    estimated_fee=50000,
                    expected_headcount=5,
                )
            )
        cls.recruitments = Recruitment.objects.bulk_create(recruitments)

        applications = []
        status_count = 0
        for recm in cls.recruitments:
            for user in cls.users:
                applications.append(
                    Application(
                        recruitment=recm,
                        user=user,
                        objective="test objective",
                        motivation="test motivation",
                        self_introduction="test self introduction",
                        available_time="test available time",
                        status=cls.status[status_count],
                    )
                )
                status_count = (status_count + 1) % 4
        cls.applications = Application.objects.bulk_create(applications)

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.users[self.USER_COUNT - 1])

    def test_admin_aply_list(self) -> None:
        url = reverse("admin-application-list")

        # 기본 조회
        query_params: Dict[str, Union[int, str]] = {"limit": 5}
        res = self.client.get(url, query_params)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], self.APPLICATION_COUNT)
        result = res.data["results"]
        self.assertEqual(
            result[0]["recruitment_title"], self.applications[self.APPLICATION_COUNT - 1].recruitment.title
        )

        # 오래된 순 정렬 기능
        query_params_order: Dict[str, Union[int, str]] = {"limit": 5, "ordering": "created_at"}
        res = self.client.get(url, query_params_order)
        self.assertEqual(res.status_code, 200)
        result = res.data["results"]
        self.assertEqual(result[0]["recruitment_title"], self.applications[0].recruitment.title)

        # 필터링 기능
        query_params_filter: Dict[str, Union[int, str]] = {"limit": 5, "status": self.status[0]}
        res = self.client.get(url, query_params_filter)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], self.APPLICATION_COUNT // 4)

    def test_admin_list_search(self) -> None:
        url = reverse("admin-application-list")

        # 공고명
        query_params_title: Dict[str, Union[int, str]] = {"limit": 5, "search": self.recruitments[0].title}
        res = self.client.get(url, query_params_title)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], self.USER_COUNT)

        # 지원자 닉네임
        query_params_nickname: Dict[str, Union[int, str]] = {"limit": 5, "search": self.users[0].nickname}
        res = self.client.get(url, query_params_nickname)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], self.RECRUITMENT_COUNT)

        # 지원자 이메일
        query_params_email: Dict[str, Union[int, str]] = {"limit": 5, "search": self.users[0].email}
        res = self.client.get(url, query_params_email)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], self.RECRUITMENT_COUNT)

    def test_admin_detail(self) -> None:
        url = reverse("admin-application-detail", kwargs={"application_id": self.applications[0].id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["id"], self.applications[0].id)
        self.assertEqual(res.data["recruitment"]["headcount"], 2)
