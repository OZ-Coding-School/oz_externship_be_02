from datetime import date, timedelta

from django.db import transaction
from django.test import TransactionTestCase
from django.utils import timezone

from apps.applications.models.applications import Application
from apps.notifications.models import Notification
from apps.recruitments.models.recruitments import Recruitment
from apps.studies.models import GroupMember
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

        self.assertTrue(n.back_url_link.endswith(f"/my-page/applications"))

    def test_notification_created_after_accept_status_change(self) -> None:
        """
        Application 상태가 PENDING -> ACCEPTED로 바뀌면
        on_commit 이후 지원자에게 승인 알림이 생성되는지 검증
        """
        # PENDING으로 생성
        with transaction.atomic():
            app = Application.objects.create(
                recruitment=self.recruitment,
                user=self.applicant,
                objective="파이썬 심화",
                motivation="깊게 배우고 싶어서",
                self_introduction="열심히 하겠습니다",
                available_time="주중 저녁",
                has_study_experience=False,
                status=Application.ApplicationStatus.PENDING,
            )

        with transaction.atomic():
            app.status = Application.ApplicationStatus.ACCEPTED
            app.save(update_fields=["status"])

        notifs = Notification.objects.filter(
            user_id=self.applicant.id,
            notification_type=Notification.NotificationType.APPLICATION_ACCEPT,
        )
        self.assertEqual(notifs.count(), 1)

        n = notifs.first()
        assert n is not None  # mypy
        self.assertIn(self.recruitment.title, n.content)
        self.assertEqual(n.back_url_link, "/my-page/applications")

        # 같은 상태로 한 번 더 저장해도 추가 생성되지 않음(중복 방지)
        with transaction.atomic():
            app.status = Application.ApplicationStatus.ACCEPTED
            app.save(update_fields=["status"])
        self.assertEqual(notifs.count(), 1)

    def test_notification_created_after_reject_status_change(self) -> None:
        """
        Application 상태가 PENDING -> REJECTED로 바뀌면
        on_commit 이후 지원자에게 거절 알림이 생성되는지 검증
        """
        # PENDING으로 생성
        with transaction.atomic():
            app = Application.objects.create(
                recruitment=self.recruitment,
                user=self.applicant,
                objective="파이썬 심화",
                motivation="깊게 배우고 싶어서",
                self_introduction="열심히 하겠습니다",
                available_time="주중 저녁",
                has_study_experience=False,
                status=Application.ApplicationStatus.PENDING,
            )

        # 상태를 REJECTED로 변경 (created=False)
        with transaction.atomic():
            app.status = Application.ApplicationStatus.REJECTED
            app.save(update_fields=["status"])

        # 지원자에게 거절 알림 1건 생성
        notifs = Notification.objects.filter(
            user_id=self.applicant.id,
            notification_type=Notification.NotificationType.APPLICATION_REJECT,
        )
        self.assertEqual(notifs.count(), 1)
        n = notifs.first()
        assert n is not None
        self.assertIn(self.recruitment.title, n.content)
        self.assertEqual(n.back_url_link, "/my-page/applications")

        # 같은 상태로 한 번 더 저장해도 추가 생성되지 않음(중복 방지)
        with transaction.atomic():
            app.status = Application.ApplicationStatus.REJECTED
            app.save(update_fields=["status"])
        self.assertEqual(notifs.count(), 1)

    def test_notification_created_after_accept_status_change_by_study_join(self) -> None:
        """
        Application 상태가 PENDING -> ACCEPTED로 바뀌면
        on_commit 이후 기존 스터디 그룹원에게 신규 인원이 있다는 알림 발생
        """
        # 기존 멤버
        old_member = User.objects.create_user(
            email="oldmember@example.com",
            password="pass1234!",
            nickname="oz",
            name="Old Member",
            phone_number="01012341222",
            gender="male",
            birthday=date(1993, 1, 1),
        )
        # 리더
        GroupMember.objects.create(study_group=self.recruitment.study_group, user=self.leader, is_leader=True)

        # 기존 멤버
        GroupMember.objects.create(study_group=self.recruitment.study_group, user=old_member, is_leader=False)

        with transaction.atomic():
            app_old = Application.objects.create(
                recruitment=self.recruitment,
                user=old_member,
                objective="파이썬 심화",
                motivation="깊게 배우고 싶어서",
                self_introduction="열심히 하겠습니다",
                available_time="주중 저녁",
                has_study_experience=False,
                status=Application.ApplicationStatus.PENDING,
            )

        with transaction.atomic():
            app_old.status = Application.ApplicationStatus.ACCEPTED
            app_old.save(update_fields=["status"])

        # 신규 멤버 accept
        with transaction.atomic():
            app_new = Application.objects.create(
                recruitment=self.recruitment,
                user=self.applicant,
                objective="파이썬 심화2",
                motivation="깊게 배우고 싶어서2",
                self_introduction="열심히 하겠습니다2",
                available_time="주중 저녁2",
                has_study_experience=False,
                status=Application.ApplicationStatus.PENDING,
            )

        with transaction.atomic():
            app_new.status = Application.ApplicationStatus.ACCEPTED
            app_new.save(update_fields=["status"])

        notifs = Notification.objects.filter(
            notification_type=Notification.NotificationType.STUDY_JOIN,
        )
        self.assertGreaterEqual(notifs.count(), 2)  # 기존 멤버(old_member)와 그룹 리더(self.leader)에게 알림 생성

        recipients = set(notifs.values_list("user_id", flat=True))
        self.assertIn(old_member.id, recipients)
        self.assertIn(self.leader.id, recipients)
        self.assertNotIn(self.applicant.id, recipients)

        n_old = notifs.filter(user_id=old_member.id).first()
        assert n_old is not None  # mypy
        self.assertIn(self.recruitment.study_group.name, n_old.content)
        self.assertIn(self.applicant.nickname, n_old.content)
        group_id = self.recruitment.study_group_id
        self.assertEqual(n_old.back_url_link, f"/study-group/{group_id}/chat")
