import logging
from datetime import date, datetime
from typing import Any, Dict, List

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from apps.studies.models import GroupMember, StudyGroup
from apps.studies.serializers.study_group import StudyCreateSerializer
from apps.users.models.user import User

logger = logging.getLogger(__name__)

user_data = {
    "name": "kimshineday",
    "nickname": "김빛날",
    "email": "kimshineday@testemail.com",
    "phone_number": "01000000000",
    "gender": "F",
    "birthday": date(2000, 1, 1),
}


class CreateStudyGroupTestFalse(TestCase):
    """
    * test 실패
        - 스터디 그룹 생성 시, 잘못된 데이터 입력. 누락된 값이 있을 경우.
        - 스터디 그룹 생성 시, 유저 데이터 없을 경우.
        - 검증 시 False 출력
    """

    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.request = self.factory.post("/fakefakefake/")
        self.request.user = User.objects.create(**user_data)

    def test_create_fail(self) -> None:
        fail_data: List[Dict[str, Any]] = [
            {"study_group": {}},  # 깡통 데이터
            {
                "study_group": {  # 스터디 기간 조건 X
                    "name": "테스트",
                    "introduction": "스터디그룹 생성 테스트 진행 중",
                    "max_headcount": 4,
                    "profile_img_url": "http://imgimgimgimg.png",
                    "start_at": datetime(2025, 9, 28),
                    "end_at": datetime(2025, 9, 30),
                }
            },
        ]

        for case in fail_data:
            serializer = StudyCreateSerializer(data=case["study_group"])
            serializer.is_valid(raise_exception=False)


class CreateStudyGroupTestSuccess(TestCase):
    """
    데이터 입력.
    test_create_group2 : 이미지 url 생략
    test_create_group3 : 이미지 url 포함
    """

    def setUp(self) -> None:
        """
        가상 user data 생성
        """
        # 스터디 그룹 생성 시, 생성자를 그룹 리더로 저장하기 위해 시리얼라이저에서 그룹 데이터 저장 후에 멤버 저장 로직까지 구현완료
        # serializer 에서 유저 데이터를 request.user로 가져오는데, 이를 위해서 테스트용 request 객체 생성하는 APIRequestFactory 모듈을 사용함.
        self.factory = APIRequestFactory()
        self.request = self.factory.post("/fakefakefake/")
        self.request.user = User.objects.create(**user_data)

    def test_create_success(self) -> None:  # 테스트 성공, 이미지 url 생략
        success_data = [
            {
                "create_data": {
                    "study_group": {
                        "name": "테스트 성공기원 1",
                        "introduction": "이미지 필수 아니여서 제외.",
                        "max_headcount": 3,
                        "start_at": datetime(2025, 10, 15),
                        "end_at": datetime(2025, 10, 30),
                    }
                },
            },
            {
                "create_data": {
                    "study_group": {
                        "name": "테스트 성공기원 2",
                        "introduction": "스터디 그룹 프로필 이미지 추가.",
                        "max_headcount": 3,
                        "profile_img_url": "http://imgimgimgimg.png",  # 이미지 값 추가
                        "start_at": datetime(2025, 10, 15),
                        "end_at": datetime(2025, 10, 30),
                    }
                },
            },
        ]

        for case in success_data:
            serializer = StudyCreateSerializer(
                data=case["create_data"],
            )
            self.assertTrue(serializer.is_valid())

            # 데이터 객체 생성
            check = serializer.save(user=self.request.user)

    def tearDown(self) -> None:
        """
        test db에 저장된 데이터 확인
        :return: data
        """
        all_groups = StudyGroup.objects.all().values()
        all_members = GroupMember.objects.all().values()
        logger.debug(f"Groups: {all_groups}")
        logger.debug(f"Members: {all_members}")


class CreateStudyGroupAPITestFail(APITestCase):
    """
    post 요청을 통해 스터디 그룹 생성하지 못하는 테스트
    """

    def setUp(self) -> None:
        """
        가상 user data 생성
        """
        self.url = reverse("create_study_group")  # 라우터 설정
        self.user = User.objects.create(**user_data)  # 가상 유저 데이터 생성
        self.client.force_authenticate(user=self.user)  # 유저 로그인

    def test_post_fail(self) -> None:
        """
        스터디 그룹 작성 API, post 요청 테스트
        결과 값 400
        :return:
        """
        fail_data = [
            {
                "name": "API 실패 테스트 1",
                "introduction": "인원 초과",
                "max_headcount": 11,
                "start_at": "2025-10-15T00:00:00Z",
                "end_at": "2025-10-30T00:00:00Z",
            },
            {
                "name": "API 실패 테스트 2",
                "introduction": "일정 설정 오류 - 시작날이 오늘 / 오늘 이후",
                "max_headcount": 6,
                "start_at": "2025-09-01T00:00:00Z",
                "end_at": "2025-09-30T00:00:00Z",
            },
            {
                "name": "API 실패 테스트 3",
                "introduction": "일정 설정 오류 - 끝나는 날짜가 시작날보다 이전",
                "max_headcount": 6,
                "start_at": "2025-10-30T00:00:00Z",
                "end_at": "2025-10-15T00:00:00Z",
            },
            {
                "name": "API 실패 테스트 4",
                "introduction": "일정 설정 오류 - 스터디는 최소 5일 진행",
                "max_headcount": 6,
                "start_at": "2025-10-01T00:00:00Z",
                "end_at": "2025-10-03T00:00:00Z",
            },
        ]

        for case in fail_data:
            response = self.client.post(self.url, data=case, format="json")
            self.assertEqual(response.status_code, 400)


class CreateStudyGroupAPITest(APITestCase):
    """
    post 요청을 통해 스터디 그룹을 생성하는 테스트
    """

    def setUp(self) -> None:
        self.url = reverse("create_study_group")  # 라우터 설정
        self.user = User.objects.create(**user_data)  # 가상 유저 데이터 생성
        self.client.force_authenticate(user=self.user)  # 유저 로그인

    def test_post_success(self) -> None:
        """
        스터디 그룹 작성 API, post 요청 테스트
        결과 값 201
        :return:
        """
        success_data = {
            "name": "Python 개념 잡기",
            "introduction": "Python 언어 기초를 공부, 프로그래머스 문제 풀기.",
            "max_headcount": 5,
            "profile_img_url": "http://imgimgimgimg.png",  # 이미지 값 추가
            "start_at": "2025-10-15T00:00:00Z",
            "end_at": "2025-10-30T00:00:00Z",
        }

        response = self.client.post(self.url, data=success_data, format="json")
        self.assertEqual(response.data["name"], "Python 개념 잡기")
        self.assertEqual(StudyGroup.objects.count(), 1)

    def tearDown(self) -> None:
        """
        test db에 저장된 데이터 확인
        :return:  data
        """
        all_groups = StudyGroup.objects.all().values()
        all_members = GroupMember.objects.all().values()
        logger.debug(f"Groups: {all_groups}")
        logger.debug(f"Members: {all_members}")
