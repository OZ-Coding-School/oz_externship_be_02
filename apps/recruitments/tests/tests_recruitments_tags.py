from unittest.mock import patch
from django.urls import reverse
from rest_framework import status, serializers
from rest_framework.test import APITestCase

from apps.recruitments.models.tags import Tag
from apps.recruitments.serializers.tags_serializers import TagSerializer
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
        url = reverse("tag-list")
        data = {"name": "new_tag"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Tag.objects.filter(name="new_tag").exists())

    def test_create_tag_unauthenticated(self) -> None:
        """태그 생성 실패 테스트 (미인증)"""
        self.client.logout()
        url = reverse("tag-list")
        data = {"name": "another_tag"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tag_duplicate_name(self) -> None:
        """
        태그 생성 실패 테스트 (이름 중복)
        - 밸리데이터 활성화 시 400 Bad Request 반환 확인
        """
        # Given: 이미 존재하는 태그
        Tag.objects.create(name="Existing Tag")

        url = reverse("tag-list")

        # When: 중복된 이름으로 태그 생성 요청
        data = {"name": "Existing Tag"}
        response = self.client.post(url, data, format="json")

        # Then: 400 Bad Request 반환 및 에러 메시지 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_create_tag_blank_name(self) -> None:
        """태그 생성 실패 테스트 (빈 이름)"""
        url = reverse("tag-list")
        data = {"name": ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 2. 태그 목록 조회 및 검색 테스트
    def test_list_tags_success(self) -> None:
        """태그 목록 조회 성공 테스트 (페이지네이션)"""
        url = reverse("tag-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 페이지네이션(5개)이 적용되었는지 확인
        self.assertEqual(len(response.data["results"]), 5)
        # 전체 태그 개수 확인
        self.assertEqual(response.data["count"], 56)

    def test_search_tags_success(self) -> None:
        """태그 검색 성공 테스트"""
        url = reverse("tag-list") + "?search=fastapi"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "fastapi")

    def test_list_tags_unauthenticated(self) -> None:
        """태그 목록 조회 실패 테스트 (미인증)"""
        self.client.logout()
        url = reverse("tag-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TagSerializerProfanityValidationTests(APITestCase):
    """
    TagSerializer의 욕설 필터링 유효성 검증(validate_name)을 테스트한다.
    """

    def test_clean_tag_passes_validation(self) -> None:
        """
        [성공] 욕설이 없는 단어가 유효성 검사를 통과하는지 확인한다.
        (규칙 기반, 모델 기반 모두 통과)
        """
        data = {"name": "클린태그"}
        serializer = TagSerializer(data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_rule_based_profanity_fails(self) -> None:
        """
        [실패] badwords.py 목록에 있는 단어가 규칙 기반 필터에서 실패하는지 확인한다.
        """
        data = {"name": "이런씨발"}
        serializer = TagSerializer(data=data)
        with self.assertRaises(serializers.ValidationError) as cm:
            serializer.is_valid(raise_exception=True)

        detail = cm.exception.detail
        if isinstance(detail, dict):
            self.assertEqual(detail['name'], ["태그에 욕설이나 비속어를 포함할 수 없습니다."])
        else:
            self.fail("ValidationError.detail이 예상과 달리 dict 타입이 아닙니다.")

    @patch("apps.recruitments.serializers.tags_serializers.PROFANITY_WORD_LIST", [])
    def test_model_based_profanity_fails(self) -> None:
        """
        [실패] 규칙 기반 목록을 통과해도, 모델 기반 필터에서 실패하는지 확인한다.
        """
        data = {"name": "fucking awesome"}
        serializer = TagSerializer(data=data)
        with self.assertRaises(serializers.ValidationError) as cm:
            serializer.is_valid(raise_exception=True)

        detail = cm.exception.detail
        if isinstance(detail, dict):
            self.assertEqual(detail['name'], ["태그에 욕설이나 비속어를 포함할 수 없습니다."])
        else:
            self.fail("ValidationError.detail이 예상과 달리 dict 타입이 아닙니다.")