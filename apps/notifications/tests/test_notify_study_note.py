from datetime import date, timedelta

from django.db import transaction
from django.test import Client, TransactionTestCase
from django.utils import timezone

from apps.notifications.models import Notification
from apps.studies.models.group_members import GroupMember
from apps.studies.models.study_groups import StudyGroup
from apps.study_notes.models.study_notes import StudyNote
from apps.users.models.user import User


class StudyNoteNotificationTests(TransactionTestCase):
    def setUp(self) -> None:
        self.client = Client()

        self.author = User.objects.create_user(
            email="oz@example.com",
            password="1q2w3e4r!",
            nickname="author",
            name="Author",
            phone_number="01000000000",
            gender="male",
            birthday=date(1990, 1, 1),
        )
        self.member1 = User.objects.create_user(
            email="ox@example.com",
            password="1q2w3e4r@",
            nickname="m1",
            name="Member1",
            phone_number="01011111111",
            gender="male",
            birthday=date(1993, 1, 1),
        )
        self.member2 = User.objects.create_user(
            email="oc@example.com",
            password="1q2w3e4r#",
            nickname="m2",
            name="Member2",
            phone_number="01022222222",
            gender="male",
            birthday=date(1994, 1, 1),
        )

        now = timezone.now()
        self.group = StudyGroup.objects.create(
            name="Python 기초 스터디", max_headcount=10, start_at=now, end_at=now + timedelta(days=30)
        )

        # 그룹 멤버(작성자 포함) 등록
        GroupMember.objects.create(study_group=self.group, user=self.author, is_leader=True)
        GroupMember.objects.create(study_group=self.group, user=self.member1, is_leader=False)
        GroupMember.objects.create(study_group=self.group, user=self.member2, is_leader=False)

    def test_notify_on_record_create(self) -> None:
        with transaction.atomic():
            StudyNote.objects.create(
                study_group=self.group,
                author=self.author,
                title="1주차",
                content="내용",
            )

        notifs = Notification.objects.filter(notification_type=Notification.NotificationType.STUDY_NOTE_CREATE)
        recipients = set(notifs.values_list("user_id", flat=True))
        self.assertEqual(recipients, {self.member1.id, self.member2.id})

        n1 = notifs.filter(user_id=self.member1.id).first()
        assert n1 is not None
        self.assertIn(self.author.nickname, n1.content)
        self.assertIn(self.group.name, n1.content)
        self.assertEqual(n1.back_url_link, f"/study-group/{self.group.uuid}")
        self.assertFalse(n1.is_read)
