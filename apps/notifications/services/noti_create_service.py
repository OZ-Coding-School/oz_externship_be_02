from datetime import date, datetime, time, timedelta
from typing import Dict, Iterable, List, Set, Tuple

from django.db import transaction
from django.db.models import Prefetch, QuerySet
from django.utils import timezone

from apps.applications.models.applications import Application
from apps.notifications.models import Notification
from apps.studies.models import GroupMember, StudyGroup
from apps.study_notes.models import StudyNote


class ApplicationNotificationService:
    def __init__(self, app: Application):
        self.app = app

    @classmethod
    def from_instance(cls, app: Application) -> "ApplicationNotificationService":
        return cls(app)

    @classmethod
    def from_id(cls, app_id: int) -> "ApplicationNotificationService":
        app = Application.objects.select_related("recruitment__author", "recruitment__study_group", "user").get(
            pk=app_id
        )
        return cls(app)

    def notify_add_application(self) -> Notification:
        rec = self.app.recruitment
        if rec is None:  # mypy
            raise ValueError("Application.recruitment is None")

        return Notification.objects.create(
            user_id=rec.author_id,
            content=f"{rec.title} 구인 공고에 신규 지원자가 있습니다.",
            notification_type=Notification.NotificationType.ADD_APPLICATION,
            back_url_link=f"/recruitments/{rec.uuid}/applications",
        )

    def notify_application_accept(self) -> Notification:
        if self.app.status != Application.ApplicationStatus.ACCEPTED:
            raise ValueError("Application status is not accepted")

        rec = self.app.recruitment
        if rec is None:
            raise ValueError("Recruitment is None")

        return Notification.objects.create(
            user_id=self.app.user_id,
            content=f"{rec.title} 구인 공고에 대한 지원 내역이 승인 되었습니다.",
            notification_type=Notification.NotificationType.APPLICATION_ACCEPT,
            back_url_link=f"/my-page/applications",
        )

    def notify_application_reject(self) -> Notification:
        if self.app.status != Application.ApplicationStatus.REJECTED:
            raise ValueError("Application.status is not REJECTED")

        rec = self.app.recruitment
        if rec is None:
            raise ValueError("Application.recruitment is None")

        return Notification.objects.create(
            user_id=self.app.user_id,  # 수신자 = 지원자
            content=f"{rec.title} 구인 공고에 대한 지원 내역이 거절되었습니다.",
            notification_type=Notification.NotificationType.APPLICATION_REJECT,
            back_url_link="/my-page/applications",
        )

    def notify_group_members_join(self) -> int:
        if self.app.status != Application.ApplicationStatus.ACCEPTED:
            return 0
        rec = self.app.recruitment
        if rec is None:  # mypy
            return 0
        group = rec.study_group

        new_user = self.app.user

        # 그룹에 참여중인 멤버들
        accepted_user_ids = set(GroupMember.objects.filter(study_group=group.id).values_list("user_id", flat=True))

        accepted_user_ids.discard(new_user.id)
        if not accepted_user_ids:
            return 0

        notifications = [
            Notification(
                user_id=uid,
                content=f"{group.name}에 {new_user.nickname} 님이 참여했습니다. 환영해주세요!",
                notification_type=Notification.NotificationType.STUDY_JOIN,
                back_url_link=f"/study-groups/{group.id}/chat",
            )
            for uid in accepted_user_ids
        ]

        with transaction.atomic():
            created = Notification.objects.bulk_create(notifications)

        return len(created)


class StudyNoteNotificationService:
    def __init__(self, sn: StudyNote):
        self.sn = sn

    @classmethod
    def from_instance(cls, sn: StudyNote) -> "StudyNoteNotificationService":
        return cls(sn)

    @classmethod
    def from_id(cls, sn_id: int) -> "StudyNoteNotificationService":
        sn = StudyNote.objects.select_related("author", "study_group").get(pk=sn_id)
        return cls(sn)

    def notify_add_study_note(self) -> int:
        group = self.sn.study_group
        author = self.sn.author
        accepted_user_ids = set(GroupMember.objects.filter(study_group=group.id).values_list("user_id", flat=True))

        accepted_user_ids.discard(author.id)
        if not accepted_user_ids:
            return 0

        notifications = [
            Notification(
                user_id=uid,
                content=f"{author.nickname} 님이 {group.name}에 스터디 기록을 작성하였습니다. 확인해보세요!",
                notification_type=Notification.NotificationType.STUDY_NOTE_CREATE,
                back_url_link=f"/study-group/{group.uuid}",
            )
            for uid in accepted_user_ids
        ]

        with transaction.atomic():
            created = Notification.objects.bulk_create(notifications)

        return len(created)


class StudyReviewNotificationService:
    @classmethod
    def day_range(cls, d: date) -> Tuple[datetime, datetime]:
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.combine(d, time.min), tz)
        end = start + timedelta(days=1)
        return start, end

    @classmethod
    def get_groups_end(cls, d: date) -> QuerySet[StudyGroup]:
        """
        로컬일자에 종료되는 그룹만 조회
        멤버 user_id를 N+1 없이 쓰도록 prefetch
        """
        start, end = cls.day_range(d)
        return (
            StudyGroup.objects.filter(end_at__gte=start, end_at__lt=end)
            .only("id", "uuid", "name")
            .prefetch_related(
                Prefetch(
                    "groupmember_set",
                    queryset=GroupMember.objects.only("id", "user_id", "study_group_id"),
                )
            )
        )

    @classmethod
    def list_notified_users(cls, today: date, user_ids: Iterable[int]) -> Set[int]:
        if not user_ids:
            return set()

        start, end = cls.day_range(today)
        return set(
            Notification.objects.filter(
                notification_type=Notification.NotificationType.STUDY_REVIEW_REQUEST,
                back_url_link="/my-page/completed-study",
                created_at__gte=start,
                created_at__lt=end,
                user_id__in=set(user_ids),
            ).values_list("user_id", flat=True)
        )

    @classmethod
    def notify_study_review(cls, study_group_name: str, target_user_ids: Iterable[int]) -> int:
        ids = set(target_user_ids)
        if not ids:
            return 0

        notifications = [
            Notification(
                user_id=uid,
                content=f"오늘은 {study_group_name}의 종료일이에요! 스터디 후기를 기록해주세요!",
                notification_type=Notification.NotificationType.STUDY_REVIEW_REQUEST,
                back_url_link=f"/my-page/completed-study",
            )
            for uid in ids
        ]

        Notification.objects.bulk_create(notifications, batch_size=1000)
        return len(notifications)

    @classmethod
    def create_review_request_notifications_for_group(cls, group: StudyGroup, today: date) -> int:
        member_ids: Set[int] = {m.user_id for m in group.groupmember_set.all()}
        if not member_ids:
            return 0

        already: Set[int] = cls.list_notified_users(today=today, user_ids=member_ids)
        targets: List[int] = [uid for uid in member_ids if uid not in already]
        if not targets:
            return 0

        return cls.notify_study_review(
            study_group_name=group.name,
            target_user_ids=targets,
        )

    @classmethod
    def create_review_request_notifications_for_due_group(
        cls, today: date | None = None, chunk_size: int = 200
    ) -> Dict[str, int]:
        """
        오늘 종료되는 모든 그룹에 대해 후기요청 멱등 발송.
        반환: {"groups_processed": X, "notifications_created": Y}
        """
        if today is None:
            today = timezone.localdate()

        groups = cls.get_groups_end(today)

        stats: Dict[str, int] = {"groups_processed": 0, "notifications_created": 0}

        for group in groups.iterator(chunk_size=chunk_size):
            created = cls.create_review_request_notifications_for_group(group=group, today=today)
            stats["groups_processed"] += 1
            stats["notifications_created"] += created

        return stats
