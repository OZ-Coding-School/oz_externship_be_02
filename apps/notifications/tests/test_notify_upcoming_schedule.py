from __future__ import annotations

from datetime import date, time, timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services.noti_create_service import (
    ScheduleUpComingNotificationService as Svc,
)
from apps.notifications.tasks import notify_upcoming_schedules
from apps.studies.models.group_members import GroupMember
from apps.studies.models.study_groups import StudyGroup
from apps.study_group_schedules.models import GroupSchedule
from apps.users.models.user import User


@override_settings(TIME_ZONE="Asia/Seoul")
class ScheduleUpComigNotificationTests(TestCase):
    def setUp(self) -> None:
        self.group = StudyGroup.objects.create(
            name="Python 기초 스터디",
            introduction="intro",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now(),
            status=StudyGroup.StatusChoices.PENDING,
        )
        self.u1 = User.objects.create_user(
            email="oz@example.com",
            password="1q2w3e4r!",
            nickname="author",
            name="Author",
            phone_number="01000000000",
            gender="male",
            birthday=date(1990, 1, 1),
        )
        self.u2 = User.objects.create_user(
            email="ox@example.com",
            password="1q2w3e4r@",
            nickname="m1",
            name="Member1",
            phone_number="01011111111",
            gender="male",
            birthday=date(1993, 1, 1),
        )
        self.u3 = User.objects.create_user(
            email="oc@example.com",
            password="1q2w3e4r#",
            nickname="m2",
            name="Member2",
            phone_number="01022222222",
            gender="male",
            birthday=date(1994, 1, 1),
        )

        self.m1 = GroupMember.objects.create(study_group=self.group, user=self.u1, is_leader=True)
        self.m2 = GroupMember.objects.create(study_group=self.group, user=self.u2, is_leader=False)
        self.m3 = GroupMember.objects.create(study_group=self.group, user=self.u3, is_leader=False)

        # 오늘/내일 기준 날짜
        self.today = timezone.localdate()
        self.tomorrow = self.today + timedelta(days=1)

    def add_participants(self, gs: GroupSchedule) -> None:
        """
        participants(M2M=GroupMember) 채우기
        """
        gs.participants.add(self.m1, self.m2, self.m3)

    # -------- 포맷팅 테스트 --------
    def test_build_message_formats_correctly(self) -> None:
        gs = GroupSchedule.objects.create(
            study_group=self.group,
            title="자료형 학습",
            objective="목표",
            session_date=self.today,
            start_time=time(9, 30),
            end_time=time(13, 30),
        )
        msg = Svc.build_notification_content(gs)
        self.assertIn(self.group.name, msg)
        self.assertIn(gs.title, msg)

    # -------- 조회 테스트 --------
    def test_get_tomorrow_schedules_filters_by_session_date(self) -> None:
        # 오늘 스케줄 2개 / 내일 스케줄 1개
        a = GroupSchedule.objects.create(
            study_group=self.group,
            title="A",
            objective="o",
            session_date=self.today,
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        b = GroupSchedule.objects.create(
            study_group=self.group,
            title="B",
            objective="o",
            session_date=self.today,
            start_time=time(11, 0),
            end_time=time(12, 0),
        )
        c = GroupSchedule.objects.create(
            study_group=self.group,
            title="C",
            objective="o",
            session_date=self.tomorrow,
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        qs = Svc.get_tomorrow_schedules(self.today)
        ids = set(qs.values_list("id", flat=True))
        self.assertEqual(ids, {c.id})

    # -------- 단일 스케줄 발송 테스트 --------
    def test_notify_tomorrow_for_schedule_creates_notifications_for_participants(self) -> None:
        gs = GroupSchedule.objects.create(
            study_group=self.group,
            title="자료형 학습",
            objective="o",
            session_date=self.today,
            start_time=time(9, 30),
            end_time=time(13, 30),
        )
        self.add_participants(gs)

        created = Svc.notify_upcoming_schedules(gs)
        self.assertEqual(created, 3)

        rows = Notification.objects.filter(notification_type=Notification.NotificationType.UPCOMING_SCHEDULE).order_by(
            "user_id"
        )

        self.assertEqual(rows.count(), 3)
        for r in rows:
            self.assertTrue(str(self.group.id) in r.back_url_link)
            self.assertIn("내일은", r.content)

    def test_notify_tomorrow_for_schedule_when_no_participants(self) -> None:
        gs = GroupSchedule.objects.create(
            study_group=self.group,
            title="빈 스케줄",
            objective="o",
            session_date=self.today,
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        created = Svc.notify_upcoming_schedules(gs)
        self.assertEqual(created, 0)
        self.assertEqual(
            Notification.objects.filter(notification_type=Notification.NotificationType.UPCOMING_SCHEDULE).count(),
            0,
        )

    # -------- 배치(태스크) 테스트 --------
    def test_task_notify_upcomig_schedules(self) -> None:
        # 내일 스케줄 1개(3명 참가) → 총 3건
        a = GroupSchedule.objects.create(
            study_group=self.group,
            title="A",
            objective="o",
            session_date=self.today + timedelta(days=1),
            start_time=time(8, 0),
            end_time=time(10, 0),
        )
        b = GroupSchedule.objects.create(
            study_group=self.group,
            title="B",
            objective="o",
            session_date=self.today,
            start_time=time(11, 0),
            end_time=time(12, 0),
        )
        self.add_participants(a)
        self.add_participants(b)

        stats = notify_upcoming_schedules()
        self.assertEqual(stats["schedules_processed"], 1)
        self.assertEqual(stats["notifications_created"], 3)

        self.assertEqual(
            Notification.objects.filter(notification_type=Notification.NotificationType.UPCOMING_SCHEDULE).count(),
            3,
        )
