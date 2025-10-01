# oz_externship_be/apps/chat/tests/test_consumers.py
import json

from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase

from apps.studies.models import GroupMember, StudyGroup
from config.asgi import application

User = get_user_model()


class TestChatConsumer(TransactionTestCase):
    """
    ChatConsumer의 동작을 검증하는 테스트 케이스
    """

    def setUp(self) -> None:
        """테스트에 필요한 초기 데이터를 설정"""
        self.user1 = User.objects.create_user(email="user1@test.com", password="password123", nickname="user1")
        self.user2 = User.objects.create_user(email="user2@test.com", password="password123", nickname="user2")
        self.non_member_user = User.objects.create_user(
            email="nonmember@test.com", password="password123", nickname="non_member"
        )
        self.study_group = StudyGroup.objects.create(name="Test Study Group")
        GroupMember.objects.create(study_group=self.study_group, user=self.user1)
        GroupMember.objects.create(study_group=self.study_group, user=self.user2)

    async def test_connect_success_for_member(self) -> None:
        """[성공] 스터디 그룹 멤버가 WebSocket 연결을 시도하면 성공적으로 연결"""
        communicator = WebsocketCommunicator(application, f"/ws/chat/rooms/{self.study_group.uuid}/")
        communicator.scope["user"] = self.user1  # type: ignore

        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        response = await communicator.receive_from()
        event_data = json.loads(response)
        self.assertEqual(event_data["type"], "user.event")
        self.assertEqual(event_data["data"]["event_type"], "join")
        await communicator.disconnect()

    async def test_connect_fail_for_non_member(self) -> None:
        """[실패] 스터디 그룹 멤버가 아닌 사용자가 연결을 시도하면 거부"""
        communicator = WebsocketCommunicator(application, f"/ws/chat/rooms/{self.study_group.uuid}/")
        communicator.scope["user"] = self.non_member_user  # type: ignore

        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4003)

    async def test_connect_fail_for_anonymous_user(self) -> None:
        """[실패] 로그인하지 않은 사용자가 연결을 시도하면 거부"""
        communicator = WebsocketCommunicator(application, f"/ws/chat/rooms/{self.study_group.uuid}/")
        communicator.scope["user"] = AnonymousUser()  # type: ignore

        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4001)

    async def test_receive_and_broadcast_message(self) -> None:
        """[성공] 한 사용자가 보낸 메시지는 같은 그룹의 다른 사용자에게 브로드캐스트"""
        communicator1 = WebsocketCommunicator(application, f"/ws/chat/rooms/{self.study_group.uuid}/")
        communicator1.scope["user"] = self.user1  # type: ignore
        await communicator1.connect()
        await communicator1.receive_from()

        communicator2 = WebsocketCommunicator(application, f"/ws/chat/rooms/{self.study_group.uuid}/")
        communicator2.scope["user"] = self.user2  # type: ignore
        await communicator2.connect()
        await communicator2.receive_from()
        await communicator2.receive_from()

        test_message = "Hello, everyone!"
        await communicator1.send_to(text_data=json.dumps({"type": "send_message", "data": {"content": test_message}}))

        response = await communicator2.receive_from()
        message_data = json.loads(response)
        self.assertEqual(message_data["type"], "chat.message")
        self.assertEqual(message_data["data"]["content"], test_message)
        self.assertEqual(message_data["data"]["sender"]["nickname"], self.user1.nickname)

        response_self = await communicator1.receive_from()
        message_data_self = json.loads(response_self)
        self.assertEqual(message_data_self["data"]["content"], test_message)

        await communicator1.disconnect()
        await communicator2.disconnect()
