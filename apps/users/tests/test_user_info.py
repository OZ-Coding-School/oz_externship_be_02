# tests/users/test_user_info_view.py

from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.core.cache import cache
from datetime import date

from apps.users.models import User
from apps.users.services.user_info_service import  get_phone_verification_key


class UserInfoViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            profile_img_url="http://example.com/profile.jpg",
            email="test@example.com",
            password="securepassword123", # 조회할 때 불러오지는 않음
            nickname="cooluser",
            name="Imsocool",
            phone_number="01012345678",
            birthday=date(2001, 9, 22),
        )
        cls.url = reverse("user_info")

    # 로그인한 사용자가 정보 조회를 시도
    # force_authenticate() 사용으로 강제 인증
    def test_get_user_info_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # 로그인하지 않은 사용자가 정보 조회를 시도
    def test_get_user_info_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 로그인한 사용자의 정보 수정: 휴대폰 인증을 완료한 버전(성공 케이스)
    def test_patch_user_info_success(self):
        self.client.force_authenticate(user=self.user)

        # 휴대폰 인증 캐시 설정
        phone_number = "01099998888"
        cache.set(get_phone_verification_key(phone_number), True)

        # 변경할 데이터
        data = {
            "profile_img_url": "http://example.com/new_profile.jpg",
            "password": "securepassword456",
            "nickname": "newnicky",
            "phone_number": phone_number,
            "is_phone_number_verified": True,
        }

        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 데이터가 제대로 변경됐는지 DB 체크
        for key, check_data in data.items():
            self.assertEqual(response.data[key], check_data)

    # 로그인한 사용자의 정보 수정: 휴대폰 인증을 하지 않은 버전(실패 케이스)
    def test_patch_user_info_without_verification(self):
        self.client.force_authenticate(self.user)

        data = {
            "phone_number": "01011112222",
            "is_phone_number_verified": False,
        }

        response = self.client.patch(self.url, data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("휴대폰 인증이 필요합니다.", response.json()["detail"])

    def test_patch_user_info_unauthenticated(self):
        data = {
            "nickname": "anonymous",
        }

        response = self.client.patch(self.url, data, content_type="application/json")
        self.assertEqual(response.status_code, 401)
