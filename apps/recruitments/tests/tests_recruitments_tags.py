from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitments.models.tags import Tag
from apps.users.models.user import User


class TagAPITestCase(APITestCase):
    """
    태그 API (REQ-RECM-002, 008) 테스트 클래스
    """

    def setUp(self) -> None:
        """
        테스트를 위한 초기 설정.
        - 테스트 유저 생성
        - API 클라이언트 생성 및 인증
        - 초기 태그 데이터 생성
        """
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            name="테스트유저",
            nickname="테스트유저닉네임",
            phone_number="01012345678",
            gender="M",
            birthday="1990-01-01",
        )
        self.client.force_authenticate(user=self.user)

        # 테스트용 태그 6개 생성
        self.tags_to_create = ["python", "django", "react", "javascript", "fastapi", "docker"]
        for tag_name in self.tags_to_create:
            Tag.objects.create(name=tag_name)

    # 1. 신규 태그 생성 테스트
    def test_create_tag_success(self) -> None:
        """태그 생성 성공 테스트"""
        url = "/api/v1/recruitments/tags/"
        data = {"name": "new_tag"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Tag.objects.filter(name="new_tag").exists())

    def test_create_tag_unauthenticated(self) -> None:
        """태그 생성 실패 테스트 (미인증)"""
        self.client.logout()
        url = "/api/v1/recruitments/tags/"
        data = {"name": "another_tag"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tag_duplicate_name(self) -> None:
        """태그 생성 실패 테스트 (이름 중복)"""
        url = "/api/v1/recruitments/tags/"
        data = {"name": "python"}  # setUp에서 이미 생성된 태그
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_create_tag_blank_name(self) -> None:
        """태그 생성 실패 테스트 (빈 이름)"""
        url = "/api/v1/recruitments/tags/"
        data = {"name": ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 2. 태그 목록 조회 및 검색 테스트
    def test_list_tags_success(self) -> None:
        """태그 목록 조회 성공 테스트 (페이지네이션)"""
        url = "/api/v1/recruitments/tags/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 페이지네이션(5개)이 적용되었는지 확인
        self.assertEqual(len(response.data["results"]), 5)
        # 전체 태그 개수 확인
        self.assertEqual(response.data["count"], 6)

    def test_search_tags_success(self) -> None:
        """태그 검색 성공 테스트"""
        url = "/api/v1/recruitments/tags/?search=py"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 검색 결과가 1개인지 확인
        self.assertEqual(len(response.data["results"]), 1)
        # 검색된 태그의 이름이 'python'인지 확인
        self.assertEqual(response.data["results"][0]["name"], "python")

    def test_list_tags_unauthenticated(self) -> None:
        """태그 목록 조회 실패 테스트 (미인증)"""
        self.client.logout()
        url = "/api/v1/recruitments/tags/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
