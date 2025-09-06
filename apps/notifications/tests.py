from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.notifications.models import Notification


class NotificationViewsTests(APITestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email="umdong@oz.com",
            password="1q2w3e4r!",
            nickname="umdong",
            name="meoyong",
            phone_number="0123456789",
            gender="male",
            birthday=date(1996, 6, 23),
        )
        self.client.force_authenticate(user=self.user)

        now = timezone.now()

        self.num1 = Notification.objects.create(
            user=self.user,
            content="1",
            notification_type=Notification.NotificationType.STUDY_JOIN,
            is_read=True,
            back_url_link="/study/uuid",
            created_at=now - timedelta(days=2),
        )
        self.num1.save(update_fields=["created_at"])

        self.num2 = Notification.objects.create(
            user=self.user,
            content="2",
            notification_type=Notification.NotificationType.ADD_APPLICATION,
            is_read=False,
            back_url_link="/recruitments/uuid/application",
            created_at=now - timedelta(days=1),
        )
        self.num2.save(update_fields=["created_at"])

        self.num3 = Notification.objects.create(
            user=self.user,
            content="3",
            notification_type=Notification.NotificationType.TODAY_SCHEDULE,
            is_read=False,
            back_url_link="/schedules/1",
            created_at=now - timedelta(days=1),
        )
        self.num3.save(update_fields=["created_at"])
        self.url = reverse("notifications:notification-list")

    def test_list_pagination(self) -> None:
        """
        limit/offset pagination
        """
        response = self.client.get(self.url, {"limit": 2, "offset": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("count", response.data)  # 총 레코드 개수
        self.assertIn("results", response.data)  # 페이지에 담긴 항목 리스트
        self.assertIn("next", response.data)  # 다음 페이지 (없으면 null)
        self.assertIn("previous", response.data)  # 이전 페이지 (없으면 null)

        self.assertEqual(response.data["count"], 3)  # 알림 목록에 3개가 있는지
        self.assertEqual(len(response.data["results"]), 2)  # 테스트 임시로 limit에 2개 제한을 걸었기에

        first = response.data["results"][0]
        self.assertEqual(first["content"], "3")

        # 각 필드 키값 검사
        keys = {
            "notification_id",
            "content",
            "type",
            "is_read",
            "back_url_link",
            "created_at",
        }
        for item in response.data["results"]:
            self.assertTrue(keys.issubset(item.keys()))

    def test_next_page(self) -> None:
        response1 = self.client.get(self.url, {"limit": 2, "offset": 0})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response1.data["results"]), 2)
        self.assertIsNotNone(response1.data["next"])

        response2 = self.client.get(self.url, {"limit": 2, "offset": 2})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data["results"]), 1)

    def test_status_read(self) -> None:
        response = self.client.get(self.url, {"status": "read", "limit": "10", "offset": "0"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        for item in response.data["results"]:
            self.assertTrue(item["is_read"])

    def test_status_unread(self) -> None:
        response = self.client.get(self.url, {"status": "unread", "limit": "10", "offset": "0"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        for item in response.data["results"]:
            self.assertFalse(item["is_read"])

    def test_unauthenticated(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, {"limit": 10, "offset": 0})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_list_notifications(self) -> None:
    #     url = reverse("notifications:notification-list")
    #     response = self.client.get(url)
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)  # 응답 상태가 200인지
    #     self.assertIsInstance(response.data, list)  # 응답 본문이 리스트인지
    #     self.assertEqual(len(response.data), 2)  # views 모킹데이터가 2개여서 그 응답이 2개인지 확인
    #
    #     # 각 모킹응답(dict)에 반드시 있어야 하는 키값들
    #     mock_keys = {
    #         "notification_id",
    #         "content",
    #         "type",
    #         "is_read",
    #         "back_url_link",
    #         "created_at",
    #     }
    #     for item in response.data:
    #         # 각 값들의 타입 확인
    #         self.assertTrue(mock_keys.issubset(item.keys()))
    #         self.assertIsInstance(item["notification_id"], int)
    #         self.assertIsInstance(item["content"], str)
    #         self.assertIsInstance(item["type"], str)
    #         self.assertIsInstance(item["is_read"], bool)
    #         self.assertIsInstance(item["back_url_link"], str)
    #         self.assertIsInstance(item["created_at"], str)
    #         self.assertNotEqual(item["created_at"], "")  # 생성시간이 비어있지는 않는지 확인

    def test_one_read(self) -> None:
        url = reverse("notifications:notification-read", kwargs={"notification_id": 1})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")  # 204 노컨텐츠이기에 빈 문자열

    def test_all_read(self) -> None:
        url = reverse("notifications:notification-read-all")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")

    def test_unread_count(self) -> None:
        url = reverse("notifications:notification-unread-count")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("unread_count", response.data)  # unread_count 키값이 있는지 확인
        self.assertIsInstance(response.data["unread_count"], int)  # unread_count가 int면 통과
