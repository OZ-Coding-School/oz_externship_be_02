from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from google.auth import message
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

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


class ChatMessageListViewTestCase(APITestCase):
    # 채팅 메시지 목록 조회 API 테스트
    # 테스트 사용자들 생성

    def setUp(self) -> None:
        self.user1 = User.objects.create_user(
            email="user1@test.com",
            password="test1234",
            name="김가나디",
            nickname="사용자1",
            phone_number="010-2212-3524",
            gender="여자",
            birthday="2002-03-17",
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com",
            password="test12345",
            name="김고먐미",
            nickname="사용자2",
            phone_number="010-7228-7873",
            gender="남자",
            birthday="2017-03-27",
        )
        self.user3 = User.objects.create_user(
            email="user3@test.com",
            password="coding123",
            name="김토끼",
            nickname="사용자3",
            phone_number="010-6258-3502",
            gender="여자",
            birthday="2003-06-25",
        )

        # 테스트 스터디 그룹 생성
        self.study_group = StudyGroup.objects.create(
            name="테스트 채팅방",
            max_headcount=10,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )

        # 그룹 멤버 추가 (user1, user2만 참여)
        GroupMember.objects.create(user=self.user1, study_group=self.study_group, is_leader=True)
        GroupMember.objects.create(user=self.user2, study_group=self.study_group, is_leader=True)

        # 테스트 메시지를 생성
        self.messages = []
        for i in range(50):
            sender = self.user1 if i % 2 == 0 else self.user2
            message = ChatMessage.objects.create(
                sender=sender, study_group=self.study_group, content=f"테스트 메시지 {i+1}"
            )
            self.messages.append(message)

        # URL 설정 (새로운 API URL)
        self.url = reverse("chat-messages-by-room", kwargs={"study_group_uuid": str(self.study_group.uuid)})
        # 클라이언트 설정
        self.client = APIClient()

    def test_autgentication_required(self) -> None:
        # 인증 필수 테스트
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_permissions_required(self) -> None:
        # 채팅방 접근 권한 테스트
        # user3은 채팅방에 참여하지 않음
        self.client.force_authenticate(user=self.user3)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

    def test_initial_load_succese(self) -> None:
        # 최초 접속 (300개 조회) 성공 테스트
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)

        # 응답 상태 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 구조 확인
        self.assertIn("results", response.data)
        self.assertIn("fetch_info", response.data)

        # fetch_info 확인
        fetch_info = response.data["fetch_info"]
        self.assertEqual(fetch_info["is_initial_load"], True)
        self.assertEqual(fetch_info["fetch_limit"], 300)
        self.assertEqual(fetch_info["fetched_count"], 50)

        # next_cursor 없어야 함
        self.assertNotIn("next_cursor", response.data)

        # 메시지 순서 확인 (오래된 것부터 최신 순)
        message = response.data["results"]
        self.assertEqual(len(message), 50)
        self.assertEqual(message[0]["content"], "테스트 메시지 1")
        self.assertEqual(message[-1]["content"], "테스트 메시지 50")

    def test_message_structure(self) -> None:
        # 메시지 데이터 구조 테스트 (API 명세서 기준)
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)

        message = response.data["results"][0]

        # 필수 필드 확인 (API 명세서 기준)
        required_fields = ["message_id", "sender", "content", "created_at"]
        for field in required_fields:
            self.assertIn(field, message)

        # sender 구조 확인
        sender = message["sender"]
        sender_fields = ["user_uuid", "nickname", "profile_img_url"]
        for field in sender_fields:
            self.assertIn(field, sender)

        # 프로필 이미지 URL 형채 확인
        self.assertIn("~/profiles/", sender["profile_img_url"])
        self.assertIn(".png", sender["profile_img_url"])

    def test_infinite_scroll_with_cursor(self) -> None:
        # 무한 스크롤(커서 기반) 테스트 - 요구사항: 최초 300개, 이후 100개
        for i in range(50, 350):
            sender = self.user1 if i % 2 == 0 else self.user2
            ChatMessage.objects.create(sender=sender, study_group=self.study_group, content=f"테스트 메시지 {i+1}")
        self.client.force_authenticate(user=self.user1)

        # 첫번째 요청 (최초 300개)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        fetch_info = response.data["fetch_info"]
        self.assertEqual(fetch_info["is_initial_load"], True)
        self.assertEqual(fetch_info["fetch_limit"], 300)
        self.assertEqual(fetch_info["retched_count"], 300)

        # next_cursor가 있어야 함
        self.assertIn("next_cursor", response.data)
        next_cursor = response.data["next_cursor"]

        # 두번째 요청 (무한스크롤 100개)
        response2 = self.client.get(self.url, {"cursor": next_cursor})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        fetch_info2 = response2.data["fetch_info"]
        self.assertEqual(fetch_info2["is_initial_load"], False)  # 무한 스크롤 (300개씩 조회)
        self.assertEqual(fetch_info2["fetch_limit"], 100)  # 110개씩 조회
        self.assertEqual(fetch_info2["fetched_count"], 50)  # 남은 메시지

        # next_cursor가 있어야 함 (더 이상 메시지 없음)
        self.assertNotIn("next_cursor", response2.data)

    def test_integration_with_existing_chatroom_list(self) -> None:
        # 기존 채팅방 목록 API와 새로운 메시지 목록 API의 통합 테스트
        self.client.force_authenticate(user=self.user1)

        # 1. 채팅방 목록 조회 (기존 API)
        chatroom_list_url = reverse("chatroom-list")
        chatroom_response = self.client.get(chatroom_list_url)

        self.assertEqual(chatroom_response.status_code, status.HTTP_200_OK)
        chatrooms = chatroom_response.data

        # 테스트 채팅방이 목록에 있는지 확인
        test_chatroom = next((room for room in chatrooms if room["name"] == "테스트 채팅방"), None)
        self.assertIsNotNone(test_chatroom)

        if test_chatroom is None:
            self.fail("테스트 채팅방을 찾을 수 없습니다.")
            return

        # 2. 해당 채팅방의 메시지 목록 조회
        message_response = self.client.get(self.url)
        self.assertEqual(message_response.status_code, status.HTTP_200_OK)

        messages = message_response.data["results"]
        self.assertEqual(len(message), 50)

        # 채팅방 목록의 last_message와 메시지 목록의 마지막 메시지 비교
        last_message_from_list = test_chatroom["lest_message"]["content"]
        last_message_from_messages = messages[-1]["content"]  # 가장 최신 메시지

        self.assertEqual(last_message_from_list, last_message_from_messages)
