from datetime import date, datetime, time, timedelta
from typing import Tuple

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services.noti_create_service import (
    StudyReviewNotificationService as Svc,
)
from apps.notifications.tasks import study_review_requests_for_groups
from apps.studies.models.group_members import GroupMember
from apps.studies.models.study_groups import StudyGroup

User = get_user_model()


def kst_today_range() -> Tuple[date, datetime, datetime]:
    tz = timezone.get_current_timezone()
    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today, time.min), tz)
    end = start + timedelta(days=1)
    return today, start, end


class StudyReviewRequestServiceTests(TestCase):
    def setUp(self) -> None:
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

        today, start, end = kst_today_range()
        # 오늘 종료되는 그룹
        self.group = StudyGroup.objects.create(
            name="Python 기초 스터디",
            introduction=None,
            max_headcount=10,
            profile_img_url=None,
            start_at=start,
            end_at=start + timedelta(hours=12),
            status=StudyGroup.StatusChoices.ONGOING,
        )
        GroupMember.objects.create(study_group=self.group, user=self.u1, is_leader=True)
        GroupMember.objects.create(study_group=self.group, user=self.u2, is_leader=False)
        GroupMember.objects.create(study_group=self.group, user=self.u3, is_leader=False)

    def test_send_only_to_non_notified_members(self) -> None:
        """
        이미 오늘 같은 타입+링크로 알림 받은 멤버는 제외하고 나머지에게만 발송
        """
        today, _, _ = kst_today_range()

        # u2는 이미 오늘 '후기요청' 알림을 받은 상태로 세팅
        Notification.objects.create(
            user_id=self.u2.id,
            content="(seed) 오늘은 Python 기초 스터디의 종료일이에요! 스터디 후기를 기록해주세요!",
            notification_type=Notification.NotificationType.STUDY_REVIEW_REQUEST,
            back_url_link=f"/my-page/completed-study",  # 멱등 기준의 링크와 동일해야 제외됨
        )

        created = Svc.send_review_requests_for_groups(group=self.group, today=today)
        self.assertEqual(created, 2)  # u1, u3 만 새로 생성

        # 총 알림 수: 기존 1 + 새로 2 = 3
        self.assertEqual(
            Notification.objects.filter(notification_type=Notification.NotificationType.STUDY_REVIEW_REQUEST).count(),
            3,
        )

    def test_idempotent_second_run(self) -> None:
        """
        같은 날 두 번 실행해도 중복 생성되지 않아야 함
        """
        today, _, _ = kst_today_range()

        first = Svc.send_review_requests_for_groups(group=self.group, today=today)
        second = Svc.send_review_requests_for_groups(group=self.group, today=today)

        # 첫 실행: 3명 생성, 두 번째 실행: 0명
        self.assertEqual(first, 3)
        self.assertEqual(second, 0)

    def test_no_members(self) -> None:
        """
        멤버가 없으면 0 반환, 알림 생성 없음
        """
        today, start, _ = kst_today_range()
        empty_group = StudyGroup.objects.create(
            name="빈그룹",
            introduction=None,
            max_headcount=10,
            profile_img_url=None,
            start_at=start,
            end_at=start + timedelta(hours=1),
            status=StudyGroup.StatusChoices.ONGOING,
        )

        created = Svc.send_review_requests_for_groups(group=empty_group, today=today)
        self.assertEqual(created, 0)
        self.assertEqual(Notification.objects.count(), 0)


class StudyReviewRequestTaskTests(TestCase):
    def setUp(self) -> None:
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

        today, start, end = kst_today_range()

        # 오늘 종료 그룹 A (2명)
        self.group_a = StudyGroup.objects.create(
            name="A그룹",
            introduction=None,
            max_headcount=10,
            profile_img_url=None,
            start_at=start,
            end_at=start + timedelta(hours=5),
            status=StudyGroup.StatusChoices.ONGOING,
        )
        GroupMember.objects.create(study_group=self.group_a, user=self.u1, is_leader=True)
        GroupMember.objects.create(study_group=self.group_a, user=self.u2, is_leader=False)

        # 오늘 종료 그룹 B (1명)
        self.group_b = StudyGroup.objects.create(
            name="B그룹",
            introduction=None,
            max_headcount=10,
            profile_img_url=None,
            start_at=start,
            end_at=start + timedelta(hours=6),
            status=StudyGroup.StatusChoices.ONGOING,
        )
        GroupMember.objects.create(study_group=self.group_b, user=self.u3, is_leader=False)

        # 내일 종료 그룹(스킵)
        self.group_tomorrow = StudyGroup.objects.create(
            name="내일그룹",
            introduction=None,
            max_headcount=10,
            profile_img_url=None,
            start_at=start,
            end_at=end + timedelta(hours=2),  # 내일
            status=StudyGroup.StatusChoices.ONGOING,
        )
        GroupMember.objects.create(study_group=self.group_tomorrow, user=self.u1, is_leader=False)

    def test_task_creates_notifications_and_is_idempotent(self) -> None:
        stats1 = study_review_requests_for_groups()
        # A: 2건, B: 1건 → 총 3건
        self.assertEqual(stats1["groups_processed"], 2)
        self.assertEqual(stats1["notifications_created"], 3)
        self.assertEqual(
            Notification.objects.filter(notification_type=Notification.NotificationType.STUDY_REVIEW_REQUEST).count(),
            3,
        )

        # 두 번째 실행: 모두 이미 오늘 받았으므로 0건
        stats2 = study_review_requests_for_groups()
        self.assertEqual(stats2["groups_processed"], 2)  # 그래도 그룹은 두 개 처리
        self.assertEqual(stats2["notifications_created"], 0)
