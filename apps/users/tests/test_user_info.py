# tests/users/test_user_info_view.py

from datetime import date
from unittest.mock import Mock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models.user import User
from apps.users.utils.enums import VerificationPurpose


class UserInfoTest(APITestCase):
    user: User
    url: str
    edit_url: str

    @classmethod
    def setUpTestData(cls) -> None:
        # 테스트용 기본 사용자 생성
        cls.user = User.objects.create_user(
            profile_img_url="http://example.com/profile.jpg",
            email="test@example.com",
            password="securepassword123",
            nickname="cooluser",
            name="Imsocool",
            phone_number="01012345678",
            birthday=date(2001, 9, 22),
            is_active=True,  # 계정 활성화 여부를 명시적으로 지정
        )

        cls.url = reverse("user_info")  # 조회용 URL
        cls.edit_url = reverse("user_info_edit")  # 수정용 URL

    # JWT 토큰을 생성하여 사용자를 로그인 상태로 설정
    def login(self) -> None:
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    # 성공: 로그인 후 조회 완료(200)
    def test_get_user_info_success(self) -> None:
        self.login()  # 로그인
        response = self.client.get(self.url)  # 정보 조회 요청
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # 조회 성공

    # 실패: 비로그인 상태로 조회 시도(401)
    def test_get_user_info_unauthorized(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue("detail" in response.data or "error" in response.data)


class UserInfoEditTest(APITestCase):
    user: User
    url: str
    edit_url: str

    @classmethod
    def setUpTestData(cls) -> None:
        # 테스트용 기본 사용자 생성
        cls.user = User.objects.create_user(
            profile_img_url="http://example.com/profile.jpg",
            email="test@example.com",
            password="securepassword123",
            nickname="cooluser",
            name="Imsocool",
            phone_number="01012345678",
            birthday=date(2001, 9, 22),
            is_active=True,  # 계정 활성화 여부를 명시적으로 지정
        )

        cls.url = reverse("user_info")  # 조회용 URL
        cls.edit_url = reverse("user_info_edit")  # 수정용 URL

    # JWT 토큰을 생성하여 사용자를 로그인 상태로 설정
    def login(self) -> None:
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    # 성공: 수정 완료(200)
    @patch("apps.users.services.phone_service.PhoneVerificationService.is_verified", return_value=True)
    # 실제로 PhoneVerificationService를 호출하지 않고, mock으로 대체
    def test_patch_user_info_success(self, mock_is_verified: Mock) -> None:
        self.login()
        data = {
            "nickname": "newnicky",
            "password": "newsecurepassword",
            "phone_number": "01098798789",
            "verification_code": "123456",
        }

        response = self.client.patch(self.edit_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_is_verified.assert_called_once_with(
            data["phone_number"], data["verification_code"], VerificationPurpose.PROFILE_UPDATE
        )  # mock 함수가 정확히 1회만 호출되었고, 인자가 기댓값과 일치하는지 확인

    # 실패: 비로그인 상태로 수정 시도(401)
    def test_patch_user_info_unauthorized(self) -> None:
        data = {"nickname": "newnicky"}
        response = self.client.patch(self.edit_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 실패: 유효하지 않은 데이터(잘못된 필드 값 등)(400)
    def test_patch_user_info_invalid_data(self) -> None:
        self.login()
        data = {"email": "invalid-email-format"}
        response = self.client.patch(self.edit_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    # 실패: 인증 코드 누락(401) - "인증이 필요한데 하지 않았다"
    @patch("apps.users.services.phone_service.PhoneVerificationService.is_verified", return_value=False)
    # 실제로 PhoneVerificationService를 호출하지 않고, mock으로 대체
    def test_patch_user_info_without_verification_code(self, mock_is_verified: Mock) -> None:
        self.login()
        data = {"phone_number": "01011112222"}
        response = self.client.patch(self.edit_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
        mock_is_verified.assert_not_called()  # 호출되지 않았어야 함

    # 실패: 잘못된 인증 코드(400)
    @patch("apps.users.services.phone_service.PhoneVerificationService.is_verified", return_value=False)
    # 실제로 PhoneVerificationService를 호출하지 않고, mock으로 대체
    def test_patch_user_info_invalid_verification_code(self, mock_is_verified: Mock) -> None:
        self.login()
        data = {
            "phone_number": "01011112222",
            "verification_code": "wrongcode",
        }
        response = self.client.patch(self.edit_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        mock_is_verified.assert_called_once_with(
            data["phone_number"], data["verification_code"], VerificationPurpose.PROFILE_UPDATE
        )  # mock 함수가 정확히 1회만 호출되었고, 인자가 기댓값과 일치하는지 확인

    # 실패: 중복 닉네임(400)
    def test_patch_user_info_duplicate_nickname(self) -> None:
        self.login()
        # 다른 사용자 생성
        User.objects.create_user(
            profile_img_url="http://example.com/profile2.jpg",
            email="test8@example.com",
            password="securepassword128",
            nickname="alreadyin",
            name="realname",
            phone_number="01010101010",
            birthday=date(2001, 9, 25),
            is_active=True,
        )

        # 중복 닉네임
        data = {"nickname": "alreadyin"}
        response = self.client.patch(self.edit_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
