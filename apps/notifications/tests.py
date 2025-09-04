from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


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

    def test_list_notifications(self) -> None:
        url = reverse("notifications:notification-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)  # 응답 상태가 200인지
        self.assertIsInstance(response.data, list)  # 응답 본문이 리스트인지
        self.assertEqual(len(response.data), 2)  # views 모킹데이터가 2개여서 그 응답이 2개인지 확인

        # 각 모킹응답(dict)에 반드시 있어야 하는 키값들
        mock_keys = {
            "notification_id",
            "content",
            "type",
            "is_read",
            "back_url_link",
            "created_at",
        }
        for item in response.data:
            # 각 값들의 타입 확인
            self.assertTrue(mock_keys.issubset(item.keys()))
            self.assertIsInstance(item["notification_id"], int)
            self.assertIsInstance(item["content"], str)
            self.assertIsInstance(item["type"], str)
            self.assertIsInstance(item["is_read"], bool)
            self.assertIsInstance(item["back_url_link"], str)
            self.assertIsInstance(item["created_at"], str)
            self.assertNotEqual(item["created_at"], "")  # 생성시간이 비어있지는 않는지 확인

    def test_one_read(self) -> None:
        url = reverse("notifications:notification-update", kwargs={"notification_id": 1})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")  # 204 노컨텐츠이기에 빈 문자열

    def test_all_read(self) -> None:
        url = reverse("notifications:notification-read-all")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")

