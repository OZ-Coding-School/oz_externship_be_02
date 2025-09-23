from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.chat.models import ChatMessage, LastReadMessage
from apps.studies.models import GroupMember, StudyGroup
from apps.users.models import User


class ChatAPITestCase(APITestCase):
    auth_user: User
    study_groups: list[StudyGroup]
    other_users: list[User]
    list_url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.auth_user = User.objects.create_user(
            email="test@example.com",
            password="pw1234",
            name="홍길동",
            nickname="testuser",
            phone_number="010-1111-1111",
            gender="남자",
            birthday="1940-09-22",
        )

        cls.study_groups = StudyGroup.objects.bulk_create(
            [
                StudyGroup(
                    name=f"test_group{i}",
                    max_headcount=5 + i,
                    start_at=timezone.now(),
                    end_at=timezone.now() + timedelta(days=5 + i),
                )
                for i in range(1, 4)
            ]
        )
        cls.other_users = User.objects.bulk_create(
            User(
                email=f"otheruser{i}@example.com",
                password="pw1234",
                name=f"다른유저{i}",
                nickname=f"otheruser{i}",
                phone_number=f"010-1111-111{i + 1}",
                gender="남자",
                birthday="1940-09-22",
            )
            for i in range(1, 3)
        )

        group_members = []
        messages = []
        last_message_informations = []
        for group in cls.study_groups:
            for user in [cls.auth_user, *cls.other_users]:
                group_members.append(
                    GroupMember(user=user, study_group=group, is_leader=False if user == cls.auth_user else True)
                )
                for i in range(1, 4):
                    messages.append(
                        ChatMessage(
                            sender=user, study_group=group, content=f"{user.name}의 {i}번째 test message 입니다."
                        )
                    )
                    last_message_informations.append(LastReadMessage(user=user, study_group=group, message_id=i))
        ChatMessage.objects.bulk_create(messages)
        GroupMember.objects.bulk_create(group_members)
        LastReadMessage.objects.bulk_create(last_message_informations)

        cls.list_url = reverse("chatroom-list")

    def setUp(self) -> None:
        self.client = self.client_class()
        self.client.force_authenticate(user=self.auth_user)

    def test_chatroom_api_success(self) -> None:
        response = self.client.get(path=self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data

        self.assertEqual(len(response_data), 3)
        first_chatroom = response.data[0]
        second_chatroom = response.data[1]
        third_chatroom = response.data[2]

        self.assertEqual(first_chatroom["name"], self.study_groups[0].name)
        self.assertEqual(second_chatroom["name"], self.study_groups[1].name)
        self.assertEqual(third_chatroom["name"], self.study_groups[2].name)

        last_message_sender_nickname_in_first_chatroom = first_chatroom["last_message"]["sender"]["nickname"]
        last_message_content_in_first_chatroom = first_chatroom["last_message"]["content"]
        self.assertEqual(last_message_sender_nickname_in_first_chatroom, f"{self.other_users[1].nickname}")
        self.assertEqual(
            last_message_content_in_first_chatroom, f"{self.other_users[1].name}의 3번째 test message 입니다."
        )
