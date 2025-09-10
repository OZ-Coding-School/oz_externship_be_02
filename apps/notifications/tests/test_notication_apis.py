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

        notis = Notification.objects.bulk_create(
            [
                Notification(
                    user=self.user,
                    content="1",
                    notification_type=Notification.NotificationType.STUDY_JOIN,
                    is_read=True,
                    back_url_link="/study/uuid",
                    created_at=now - timedelta(days=2),
                ),
                Notification(
                    user=self.user,
                    content="2",
                    notification_type=Notification.NotificationType.ADD_APPLICATION,
                    is_read=False,
                    back_url_link="/recruitments/uuid/application",
                    created_at=now - timedelta(days=1),
                ),
                Notification(
                    user=self.user,
                    content="3",
                    notification_type=Notification.NotificationType.TODAY_SCHEDULE,
                    is_read=False,
                    back_url_link="/schedules/1",
                    created_at=now - timedelta(days=1),
                ),
            ]
        )
        self.notification = notis[0]  # 첫번째 알람을 테스트 대상으로함 / self.notification 속성 정의를 위함(119)
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

    def test_get_notification_list_on_the_next_page(self) -> None:
        response1 = self.client.get(self.url, {"limit": 2, "offset": 0})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response1.data["results"]), 2)
        self.assertIsNotNone(response1.data["next"])

        response2 = self.client.get(self.url, {"limit": 2, "offset": 2})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data["results"]), 1)

    def test_get_read_notification_list(self) -> None:
        response = self.client.get(self.url, {"is_read": "true", "limit": "10", "offset": "0"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        for item in response.data["results"]:
            self.assertTrue(item["is_read"])

    def test_get_unread_notification_list(self) -> None:
        response = self.client.get(self.url, {"is_read": "false", "limit": "10", "offset": "0"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        for item in response.data["results"]:
            self.assertFalse(item["is_read"])

    def test_get_notification_list_when_user_unauthenticated(self) -> None:
        self.client.logout()
        response = self.client.get(self.url, {"limit": 10, "offset": 0})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_read_api_for_only_one_notification(self) -> None:
        url = reverse("notifications:notification-read", kwargs={"notification_id": self.notification.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")  # 204 노컨텐츠이기에 빈 문자열
        self.notification.refresh_from_db()  # 서비스에서 save() 호출 시 실제로 바뀌는지 확인하는 테스트
        self.assertTrue(self.notification.is_read)

    def test_read_api_for_all_notification(self) -> None:
        url = reverse("notifications:notification-read-all")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        unread_exists = Notification.objects.filter(user=self.user, is_read=False).exists()
        self.assertFalse(unread_exists)  # 전체 읽음 후 미읽음 개수가 0개인지 확인

    def test_unread_count(self) -> None:
        url = reverse("notifications:notification-unread-count")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("unread_count", response.data)  # unread_count 키값이 있는지 확인
        self.assertIsInstance(response.data["unread_count"], int)  # unread_count가 int면 통과
