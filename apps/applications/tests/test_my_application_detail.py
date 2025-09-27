from datetime import datetime, timedelta

from rest_framework.test import APITestCase
from django.utils import timezone

from apps.applications.models.applications import Application
from apps.users.models.user import User
from apps.recruitments.models.recruitments import Recruitment
from apps.studies.models.study_groups import StudyGroup


class MyApplicationDetailTestCase(APITestCase):
    @classmethod
    def setUp(self):
        self.user = User.objects.create_user(
            User(
                email=f"testuser@test.com",
                password="itspassword",
                name="test",
                nickname=f"testuser",
                phone_number=f"010-0000-0000",
                gender="male",
                birthday=timezone.make_aware(datetime(2025, 9, 9)),
            )
        )
        self.client.force_authenticate(user=self.user)


        self.study_group=StudyGroup.objects.create(
            name="test group1",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=1)
        )

        self.recruitment=Recruitment.objects.create(
            study_group=self.study_group,
            author=self.user,
            title=f"test recruitment",
            content="test content",
            estimated_fee=50000,
            expected_headcount=5
        )

        self.applications=Application.objects.create(
            recruitment=self.recruitment,
            user=self.user,
            objective="test objective",
            motivation="test motivation",
            self_introduction="test self introduction",
            available_time="test available time",
            status="REJECTED"
        )