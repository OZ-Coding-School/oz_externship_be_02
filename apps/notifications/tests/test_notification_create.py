from datetime import date, timedelta

from django.db import transaction
from django.test import TransactionTestCase
from django.utils import timezone

from apps.applications.models.applications import Application
from apps.notifications.models import Notification
from apps.recruitments.models.recruitments import Recruitment
from apps.studies.models.study_groups import StudyGroup
from apps.users.models.user import User


class NotificationOnApplicationCreateTests(TransactionTestCase):
    """
    Application 생성(post_save, created=True) 시
    on_commit 이후 Notification이 생성되는지 검증
    """

    def setUp(self) -> None:
        # 작성자와 지원자
        self.leader = User.objects.create_user(
            email="leader@example.com",
            password="pass1234!",
            nickname="leader",
            name="Leader",
            phone_number="01000000000",
            gender="male",
            birthday=date(1990, 1, 1),
        )
        self.applicant = User.objects.create_user(
            email="applicant@example.com",
            password="pass1234!",
            nickname="applicant",
            name="Applicant",
            phone_number="01011111111",
            gender="male",
            birthday=date(1995, 1, 1),
        )
        now = timezone.now()
        study_group = StudyGroup.objects.create(
            name="Study", max_headcount=10, start_at=now, end_at=now + timedelta(days=30)
        )
        self.recruitment = Recruitment.objects.create(
            study_group=study_group,
            author=self.leader,
            title="API 테스트용 공고",
            content="테스트 내용",
            expected_headcount=5,
            estimated_fee=25000,
            views_count=100,
        )

    def test_notification_created_after_application_save_commit(self) -> None:
        """
        Application 생성 시 on_commit 이후 Notification 1건이 생성되고,
        수신자/타입/콘텐츠/링크가 기대값인지 검증
        """
        # when: Application 생성 (created=True)
        with transaction.atomic():
            app = Application.objects.create(
                recruitment=self.recruitment,
                user=self.applicant,
                objective="파이썬 심화",
                motivation="깊게 배우고 싶어서",
                self_introduction="열심히 하겠습니다",
                available_time="주중 저녁",
                has_study_experience=True,
                study_experience="학교 알고리즘 스터디",
                status=Application.ApplicationStatus.PENDING,
                created_at=timezone.now(),
            )

        # then: atomic 블록을 빠져나오면 on_commit 콜백이 실행됨
        notifs = Notification.objects.filter(
            user_id=self.leader.id,
            notification_type=Notification.NotificationType.ADD_APPLICATION,
        )
        self.assertEqual(notifs.count(), 1)

        n = notifs.first()
        assert n is not None  # mypy
        self.assertIn(self.recruitment.title, n.content)

        self.assertTrue(n.back_url_link.endswith(f"/recruitments/{self.recruitment.uuid}/applications"))
