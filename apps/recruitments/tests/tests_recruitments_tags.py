from django.urls import reverse  # URL 패턴의 이름(name)을 사용하여 동적으로 URL을 생성(역추적)하는 유틸리티
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

        # 테스트에 사용할 태그 데이터 준비
        tags_to_create = ["python", "django", "react", "javascript", "fastapi", "docker"]

        # 1. DB에 저장할 Tag 객체들을 파이썬 메모리 상에 리스트로 생성
        #    - 이 단계에서는 아직 데이터베이스에 접근(쿼리)하지 않는다.
        #    - 리스트 컴프리헨션을 사용하여 간결하게 표현.
        tag_objects = [Tag(name=tag_name) for tag_name in tags_to_create]

        # 2. bulk_create를 사용하여 준비된 객체 리스트를 단 한 번의 쿼리로 DB에 삽입
        Tag.objects.bulk_create(tag_objects)

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
        # """태그 생성 실패 테스트 (이름 중복)"""
        # url = "/api/v1/recruitments/tags/"
        # data = {"name": "python"}  # setUp에서 이미 생성된 태그
        # response = self.client.post(url, data)
        # self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        """
        태그 생성 실패 테스트 (이름 중복)
        - 밸리데이터 활성화 시 400 Bad Request 반환 확인
        """
        # Given: 이미 존재하는 태그
        Tag.objects.create(name="Existing Tag")

        # reverse 유틸리티는 URL을 하드코딩하는 대신, URL 패턴의 이름으로부터 동적으로 URL을 생성합니다.
        # 이 방식을 사용하면 urls.py 파일에서 URL 구조가 변경되더라도 테스트 코드를 수정할 필요가 없어 유지보수에 용이합니다.
        # 아래 코드는 recruitments 앱 네임스페이스에 속한 'tag-list'라는 이름의 URL 패턴을 찾아
        # 해당하는 URL(예: '/api/v1/recruitments/tags/')을 동적으로 생성하여 url 변수에 할당합니다.
        # 이 URL은 중복 태그 생성을 테스트하기 위한 POST 요청의 엔드포인트로 사용됩니다.
        url = reverse("recruitments:tag-list")

        # When: 중복된 이름으로 태그 생성 요청
        data = {"name": "Existing Tag"}
        response = self.client.post(url, data, format="json")

        # Then: 400 Bad Request 반환 및 에러 메시지 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # UniqueValidator의 기본 에러 메시지 확인
        self.assertIn("name", response.data)
        self.assertIn("tag의 name은/는 이미 존재합니다.", response.data["name"][0])
        # self.assertIn("tag with this name already exists.", response.data["name"][0].lower())  # 대소문자 무시

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
