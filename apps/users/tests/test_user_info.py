# tests/users/test_user_info_view.py

from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.core.cache import cache
from datetime import date

from apps.users.models import User


class UserInfoViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # 테스트용 사용자 생성
        cls.user = User.objects.create_user(
            profile_img_url="http://example.com/profile.jpg",
            email="test@example.com",
            password="securepassword123",
            nickname="cooluser",
            name="Imsocool",
            phone_number="01012345678",
            birthday=date(2001, 9, 22),
        )
        cls.url = reverse("user_info")

    def setUp(self):
        self.user = self.__class__.user
        cache.clear() # 테스트마다 인증 캐시 초기화

    # 성공: 조회 완료(200)
    def test_get_user_info_success(self):
        pass

    # 실패: 비로그인 상태로 조회 시도(401)
    def test_get_user_info_unauthorized(self):
        pass

    # 성공: 수정 완료(200)
    def test_patch_user_info_success(self):
        pass
    
    # 실패: 비로그인 상태로 수정 시도(401)
    def test_patch_user_info_unauthorized(self):
        pass

    # 실패: 유효하지 않은 데이터(잘못된 필드 값 등)(400)
    def test_patch_user_info_invalid_data(self):
        pass

    # 실패: 필수 필드 누락(400) #? 필요할까?
    def test_patch_user_info_missing_required_field(self):
        pass

    # 실패: 잘못된 인증 코드(400)
    def test_patch_user_info_invalid_verification_code(self):
        pass

    # 실패: 인증 코드 누락(400)
    def test_patch_user_info_without_verification_code(self):
        pass

    # 실패: 이미 등록된 전화번호(400/409)
    def test_patch_user_info_phone_number_duplicate(self):
        pass