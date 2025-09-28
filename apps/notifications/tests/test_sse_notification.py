from datetime import date
from unittest.mock import Mock, patch

from django.test import TestCase

from apps.notifications.models import Notification
from apps.notifications.services.noti_create_service import StudyNoteNotificationService
from apps.studies.models import GroupMember, StudyGroup
from apps.study_notes.models import StudyNote
from apps.users.models import User


class NotificationSSEReceiverTests(TestCase):
    @patch(
        "apps.notifications.receivers.send_event"
    )  # 시그널 리시버 내부에서 쓰는 send_event를 MOCK으로 바꿔치기 / 호출되는지 확인
    def test_post_save_push_sse(self, mock_send: Mock) -> None:
        u = User.objects.create_user(  # 테스트용 유저
            email="oz@example.com",
            password="1q2w3e4r!",
            nickname="author",
            name="Author",
            phone_number="01000000000",
            gender="male",
            birthday=date(1990, 1, 1),
        )
        n = Notification.objects.create(  # post_save 시그널 생성 / send_event 호출
            user=u,
            content="hello",
            notification_type=Notification.NotificationType.ADD_APPLICATION,
            back_url_link="/x",
        )
        mock_send.assert_called_once()  # 한번만 호출 됐는지 확인
        channel, event, data = mock_send.call_args.args
        assert channel == f"user-{u.id}"
        assert event == "notification"
        assert data["id"] == n.id
        assert data["type"] == "ADD_APPLICATION"
        assert data["content"] == "hello"
        assert data["back_url_link"] == "/x"
        assert data["is_read"] is False


class BulkSSETests(TestCase):
    @patch("apps.notifications.services.noti_create_service.send_event")
    def test_bulk_create_push(self, mock_send: Mock) -> None:
        with self.captureOnCommitCallbacks(execute=True):  # on_commit 콜백 지금 실행
            leader = User.objects.create_user(
                email="ox@example.com",
                password="1q2w3e4r@",
                nickname="m1",
                name="Member1",
                phone_number="01011111111",
                gender="male",
                birthday=date(1993, 1, 1),
            )
            m1 = User.objects.create_user(
                email="oc@example.com",
                password="1q2w3e4r#",
                nickname="m2",
                name="Member2",
                phone_number="01022222222",
                gender="male",
                birthday=date(1994, 1, 1),
            )
            m2 = User.objects.create_user(
                email="os@example.com",
                password="1q2w3e4r#",
                nickname="m3",
                name="Member4",
                phone_number="01033333333",
                gender="male",
                birthday=date(1995, 1, 1),
            )
            g = StudyGroup.objects.create(
                name="G",
                introduction="i",
                max_headcount=5,
                start_at="2025-01-01T00:00:00Z",
                end_at="2025-12-31T00:00:00Z",
            )
            GroupMember.objects.create(study_group=g, user=leader, is_leader=True)
            GroupMember.objects.create(study_group=g, user=m1)
            GroupMember.objects.create(study_group=g, user=m2)

            note = StudyNote.objects.create(study_group=g, author=leader, title="t", content="c")

            created = StudyNoteNotificationService.from_instance(note).notify_add_study_note()
            assert created == 2

        # send_event가 수신자별로 호출되는지 기대 채널명 확인
        channels = {args[0] for args, _ in mock_send.call_args_list}
        assert channels == {f"user-{m1.id}", f"user-{m2.id}"}
