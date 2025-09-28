from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from django.urls import reverse

from apps.applications.models.applications import Application
from apps.users.models.user import User
from apps.recruitments.models.recruitments import Recruitment
from apps.studies.models.study_groups import StudyGroup


class MyApplicationDetailTestCase(APITestCase):
    @classmethod
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@test.com",
            password="itspassword",
            name="test",
            nickname="testuser",
            phone_number="010-0000-0000",
            gender="male",
            birthday=timezone.make_aware(datetime(2025, 9, 9)),
        )
        self.client.force_authenticate(user=self.user)


        self.study_group=StudyGroup.objects.create(
            name="test group",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=1)
        )

        recruitments=[]
        for i in range(2):
            recruitments.append(Recruitment(
                study_group=self.study_group,
                author=self.user,
                title=f"test recruitment{i+1}",
                content="test content",
                estimated_fee=50000,
                expected_headcount=5
            ))
        self.recruitments=Recruitment.objects.bulk_create(recruitments)

        applications=[]
        applications.append(Application(
            recruitment=self.recruitments[0],
            user=self.user,
            objective="test objective",
            motivation="test motivation",
            self_introduction="대기중 지원",
            available_time="test available time",
            status=Application.ApplicationStatus.PENDING
        ))
        applications.append(Application(
            recruitment=self.recruitments[1],
            user=self.user,
            objective="test objective",
            motivation="test motivation",
            self_introduction="거절된 지원",
            available_time="test available time",
            status=Application.ApplicationStatus.REJECTED
        ))
        self.applications=Application.objects.bulk_create(applications)

    def test_get_my_application_detail(self):
        url=reverse("my-aply-detail-cancel", kwargs={"application_id": self.applications[0].id})
        res=self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["self_introduction"], "대기중 지원")

    def test_cancel_my_application(self):
        url=reverse("my-aply-detail-cancel", kwargs={"application_id": self.applications[0].id})
        res=self.client.patch(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        aply=Application.objects.get(id=self.applications[0].id)
        self.assertEqual(aply.status,Application.ApplicationStatus.CANCELED)

        # 대기 중이 아닌 지원내역 취소
        url=reverse("my-aply-detail-cancel", kwargs={"application_id": self.applications[1].id})
        res=self.client.patch(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        aply=Application.objects.get(id=self.applications[1].id)
        self.assertNotEqual(aply.status,Application.ApplicationStatus.CANCELED)