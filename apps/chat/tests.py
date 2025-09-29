from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.chat.models import ChatMessage, LastReadMessage
from apps.studies.models import GroupMember, StudyGroup
from apps.users.models import User


class ChatAPITestCase(APITestCase):
    auth_user: User
    study_groups: list[StudyGroup]
    other_users: list[User]
    chat_room_list_url: str
    chat_message_list_url: str

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
            [
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
            ]
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

        cls.chat_room_list_url = reverse("chatroom-list")
        cls.chat_message_list_url = reverse("message-list", kwargs={"study_group_uuid": cls.study_groups[0].uuid})

    def setUp(self) -> None:
        self.client = self.client_class()
        self.client.force_authenticate(user=self.auth_user)

    def test_chatroom_api_success(self) -> None:
        response = self.client.get(path=self.chat_room_list_url)

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

    def test_message_list_api_when_user_unauthorized(self) -> None:
        # given
        self.client.logout()
        # when
        response = self.client.get(self.chat_message_list_url)
        # then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_message_list_api_when_user_is_not_group_member(self) -> None:
        another_user = User.objects.create(
            email="another@example.com",
            password="pw1234",
            name="낯선사람",
            nickname="another",
            phone_number="010-1111-0101",
            gender="MALE",
            birthday="1999-09-22",
        )
        self.client.force_authenticate(user=another_user)
        response = self.client.get(self.chat_message_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)

    def test_message_list_api_success_without_cursor(self) -> None:
        self.client.force_authenticate(user=self.auth_user)
        response = self.client.get(self.chat_message_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        messages = response.data["results"]
        self.assertEqual(len(messages), 9)

        self.assertIn("next", response.data)

        message = response.data["results"][0]

        required_fields = ["id", "sender", "content", "created_at"]
        for field in required_fields:
            self.assertIn(field, message)

        sender_info = message["sender"]

        sender_fields = ["uuid", "nickname", "profile_img_url"]
        for field in sender_fields:
            self.assertIn(field, sender_info)

    def test_message_list_api_success_with_cursor_params(self) -> None:
        # given
        create_messages = []
        for user in [self.auth_user, *self.other_users]:
            for i in range(4, 101):
                create_messages.append(
                    ChatMessage(
                        sender=user,
                        study_group=self.study_groups[0],
                        content=f"{user.name}의 {i}번째 test message 입니다.",
                    )
                )
        ChatMessage.objects.bulk_create(create_messages)

        self.client.force_authenticate(user=self.auth_user)

        first_page_response = self.client.get(self.chat_message_list_url)

        self.assertEqual(first_page_response.status_code, status.HTTP_200_OK)

        messages = first_page_response.data["results"]
        self.assertEqual(len(messages), 100)

        self.assertIn("next", first_page_response.data)
        next_url = first_page_response.data["next"]

        parsed = urlparse(next_url)
        cursor = parse_qs(parsed.query).get("cursor", [None])[0]
        self.assertIsNotNone(cursor)

        second_page_response = self.client.get(self.chat_message_list_url, query_params={"cursor": cursor})
        self.assertEqual(second_page_response.status_code, status.HTTP_200_OK)

        messages2 = second_page_response.data["results"]
        self.assertEqual(len(messages2), 100)

        self.assertIn("next", second_page_response.data)

        first_message_in_second_page = (
            ChatMessage.objects.filter(study_group=self.study_groups[0]).order_by("-created_at", "-id")
        )[100]
        self.assertEqual(second_page_response.data["results"][0]["id"], first_message_in_second_page.id)

    def test_message_list_api_fail_when_group_uuid_invalid(self) -> None:
        invalid_uuid = "11111111-1111-1111-1111-111111111111"
        invalid_url = reverse("message-list", kwargs={"study_group_uuid": invalid_uuid})
        response = self.client.get(invalid_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
