from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.studies.models import StudyGroup, StudyReview

User = get_user_model()


class TestStudyReviewCreateAPI(APITestCase):
    """
    [REQ-REVW-001] 스터디 그룹 리뷰 작성 API
    POST /api/v1/reviews/
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com", password="1234", birthday="2000-01-01", name="테스트유저", nickname="tester"
        )
        self.client.force_authenticate(self.user)

        # 종료된 스터디 그룹
        self.study_group = StudyGroup.objects.create(
            name="테스트 스터디",
            introduction="테스트용 소개글",
            max_headcount=5,
            start_at=timezone.now() - timedelta(days=10),
            end_at=timezone.now() - timedelta(days=1),
            status=StudyGroup.StatusChoices.ENDED,
        )
        self.url = reverse("review-create")

    def test_create_review_success(self) -> None:
        # 성공 케이스
        data = {
            "study_group_id": self.study_group.id,
            "rating": 5,
            "content": "정말 유익한 스터디였습니다!",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(StudyReview.objects.count(), 1)
        self.assertEqual(response.data["content"], data["content"])

    def test_create_review_unauthenticated(self) -> None:
        # 실패: 비로그인
        client = APIClient()
        data = {"study_group_id": self.study_group.id, "rating": 5, "content": "로그인 안 했어요"}
        response = client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 401)

    def test_create_review_duplicate(self) -> None:
        # 실패: 중복 리뷰
        StudyReview.objects.create(user=self.user, study_group=self.study_group, star_rating=5, content="첫 리뷰")
        data = {"study_group_id": self.study_group.id, "rating": 5, "content": "중복 리뷰 시도"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("이미 리뷰를 작성한", str(response.data))

    def test_create_review_invalid_rating(self) -> None:
        # 실패: 잘못된 평점 일부러 존재하지않는 점수 부여함 ㅋ
        data = {"study_group_id": self.study_group.id, "rating": 10, "content": "잘못된 평점"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_create_review_not_ended_group(self) -> None:
        # 실패: 종료되지 않은 스터디 그룹
        active_group = StudyGroup.objects.create(
            name="진행중 스터디",
            introduction="아직 진행 중",
            max_headcount=5,
            start_at=timezone.now() - timedelta(days=1),
            end_at=timezone.now() + timedelta(days=7),
            status=StudyGroup.StatusChoices.ONGOING,
        )
        data = {"study_group_id": active_group.id, "rating": 5, "content": "아직 끝나지 않았어요"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("종료되지 않은", str(response.data))

    def test_create_review_triggers_create_method(self) -> None:
        # 성공 케이스에서 create() 메서드까지 실행 확인
        data = {"study_group_id": self.study_group.id, "rating": 4, "content": "create 메서드 확인"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 201)
        review = StudyReview.objects.first()
        assert review is not None  # mypy 통과용

        self.assertEqual(review.user, self.user)
        self.assertEqual(review.star_rating, 4)

    def test_create_review_exact_error_messages(self) -> None:
        # 실패 케이스에서 ValidationError 메시지 구조까지 검증
        active_group = StudyGroup.objects.create(
            name="미종료 스터디",
            introduction="테스트",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=5),
            status=StudyGroup.StatusChoices.ONGOING,
        )
        data = {
            "study_group_id": active_group.id,
            "rating": 5,
            "content": "에러 메시지 확인",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 400)

        # 기존: self.assertIn("study_group_id", response.data)
        # 수정: "detail" 키와 메시지 내용 확인
        self.assertIn("detail", response.data)
        self.assertIn(
            "종료되지 않은 스터디 그룹에는 리뷰를 작성할 수 없습니다.",
            response.data["detail"]
        )
