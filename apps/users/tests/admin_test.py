from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.tests.mixins.test_user_mixins import TestUserMixin
from apps.users.models import User

# 시리얼라이저와 서비스를 import 합니다.
from apps.users.serializers.admin_serializers import UserPermissionRequestSerializer
from apps.users.services.admin_servies import UserPermissionService

user_model = User


class UserPermissionSerializerTest(TestCase):
    # 이 테스트는 이제 시리얼라이저의 '유효성 검사' 기능만 확인합니다.
    def test_permission_request_serializer_valid_data(self) -> None:
        # 1. 유효한 데이터 테스트
        data = {"permission": "staff"}
        serializer = UserPermissionRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_permission_request_serializer_invalid_choices(self) -> None:
        # 2. 유효하지 않은 데이터 테스트
        data = {"permission": "invalid_permission"}
        serializer = UserPermissionRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("permission", serializer.errors)


class UserPermissionServiceTests(TestCase, TestUserMixin):
    # 비즈니스 로직 테스트
    def setUp(self) -> None:
        # 테스트에 필요한 유저만 생성
        self.general_user = self._create_test_user(email="user@test.com")

    def test_update_user_permission_to_admin(self) -> None:
        update_user = UserPermissionService.update_user_permission(user=self.general_user, permission="admin")
        self.assertTrue(update_user.is_superuser)
        self.assertTrue(update_user.is_staff)


class UserPermissionAPITest(APITestCase, TestUserMixin):
    # API의 모든 흐름(View-Serializer-Service)이 확인
    def setUp(self) -> None:
        self.admin_user = User.objects.create_superuser(
            email="sy_admin@test.com",
            password="418770",
            name="관리자",
            nickname="admin",
            phone_number="010-1234-5678",
            birthday="1995-05-21",
            is_active=True,
        )
        self.target_user = self._create_test_user(email="target_user@test.com")

    def test_update_permission_success_as_admin(self) -> None:
        # 관리자 로그인
        self.client.force_authenticate(user=self.admin_user)
        data = {"permission": "admin"}

        url = reverse("admin_user:user_permissions", kwargs={"user_uuid": self.target_user.uuid})

        response = self.client.patch(url, data=data, format="json")

        # 검증 로직은 기존과 동일하게 훌륭합니다.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_staff)
        self.assertTrue(self.target_user.is_superuser)
        self.assertEqual(response.data["message"], "권한이 성공적으로 변경되었습니다.")
        self.assertEqual(response.data["data"]["permission"], "admin")
