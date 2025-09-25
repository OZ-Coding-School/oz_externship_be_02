import uuid
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.studies.models import StudyGroup, StudyReview
from apps.users.models.user import User


class TestStudyReviewCreateAPI(APITestCase):
    """
    [REQ-REVW-001] 스터디 그룹 리뷰 작성 API
    POST /api/v1/reviews/
    """

    def setUp(self) -> None:
        self.client = self.client_class()
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
        self.url = reverse("review-create-list", kwargs={"group_uuid": self.study_group.uuid})

    def test_create_review_success(self) -> None:
        # 성공 케이스
        data = {
            "star_rating": 5,
            "content": "정말 유익한 스터디였습니다!",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(StudyReview.objects.count(), 1)
        self.assertEqual(response.data["content"], data["content"])

    def test_create_review_unauthenticated(self) -> None:
        # 실패: 비로그인
        self.client.logout()
        data = {"star_rating": 5, "content": "로그인 안 했어요"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 401)

    def test_create_review_duplicate(self) -> None:
        # 실패: 중복 리뷰
        StudyReview.objects.create(user=self.user, study_group=self.study_group, star_rating=5, content="첫 리뷰")
        data = {"star_rating": 5, "content": "중복 리뷰 시도"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("이미 작성된 리뷰가 있습니다.", str(response.data))

    def test_create_review_invalid_star_rating(self) -> None:
        # 실패: 잘못된 평점 일부러 존재하지않는 점수 부여함 ㅋ
        data = {"star_rating": 10, "content": "잘못된 평점"}
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
        self.url = reverse("review-create-list", kwargs={"group_uuid": active_group.uuid})
        data = {"star_rating": 5, "content": "아직 끝나지 않았어요"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("종료되지 않은", str(response.data))

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
        self.url = reverse("review-create-list", kwargs={"group_uuid": active_group.uuid})
        data = {
            "star_rating": 5,
            "content": "에러 메시지 확인",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 400)

        # "error" 키와 메시지 내용 확인
        self.assertIn("error", response.data)
        self.assertIn("종료되지 않은 스터디 그룹에는 리뷰를 작성할 수 없습니다.", response.data["error"])

    def test_create_review_when_invalid_group_uuid(self) -> None:
        self.invalid_url = reverse("review-create-list", kwargs={"group_uuid": (uuid_val := uuid.uuid4())})
        data = {
            "star_rating": 5,
            "content": "에러 메시지 확인",
        }
        response = self.client.post(self.invalid_url, data, format="json")
        self.assertEqual(response.status_code, 404)


class TestStudyGroupReviewListAPI(APITestCase):
    """
    [REQ-REVW-00] 스터디 그룹 리뷰 목록 조회 API

    검증 포인트
    - 성공: 200 OK + 응답 구조/필드/포맷
    - 성공: 리뷰 없음 -> 200 OK + 빈 리스트 (study_group_uuid 포함)
    - 실패: 잘못된 group_uuid -> 404 Not Found
    - 실패: 비인증 -> 401 Unauthorized
    """

    def setUp(self) -> None:
        self.client = self.client_class()
        self.user = User.objects.create_user(
            email="test@test.com",
            password="1234",
            birthday="2000-01-01",
            name="테스트유저",
            nickname="tester",
            phone_number="01000000001",
        )
        self.study_group = StudyGroup.objects.create(
            name="테스트 그룹",
            introduction="소개",
            max_headcount=5,
            start_at=timezone.now() - timedelta(days=10),
            end_at=timezone.now() - timedelta(days=1),
            status=StudyGroup.StatusChoices.ENDED,
        )
        self.url = reverse("review-create-list", kwargs={"group_uuid": self.study_group.uuid})

    def test_success_review_list(self) -> None:
        # 성공 케이스: 스터디 그룹 리뷰 목록 조회
        StudyReview.objects.create(
            user=self.user,
            study_group=self.study_group,
            content="정말 유익한 스터디였습니다.",
            star_rating=5,
        )

        user2 = User.objects.create_user(
            email="other@test.com",
            password="1234",
            name="다른유저",
            nickname="other",
            birthday="2001-01-01",
            phone_number="01000000002",
        )
        StudyReview.objects.create(
            user=user2,
            study_group=self.study_group,
            content="좋았지만 시간이 조금 촉박했어요.",
            star_rating=4,
        )

        resp = self.client.get(self.url, format="json")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)
        self.assertIn("study_group_uuid", resp.data[0])
        self.assertEqual(resp.data[0]["study_group_uuid"], str(self.study_group.uuid))

    def test_success_review_list_no_reviews(self) -> None:
        # 성공: 리뷰가 없는 경우 -> 200 OK + 빈 리스트 (study_group_uuid 포함)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)

    def test_fail_review_list_invalid_uuid(self) -> None:
        # 실패: 존재하지 않는 그룹 uuid (404)
        bad_url = reverse(
            "review-create-list",
            kwargs={"group_uuid": "11111111-1111-1111-1111-111111111111"},
        )
        resp = self.client.get(bad_url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class TestReviewUpdateAPI(APITestCase):
    """
    스터디 그룹 리뷰 수정 API 테스트
    PATCH /api/v1/study-groups/{group_uuid}/reviews/{review_id}
    """

    def setUp(self) -> None:
        self.client = self.client_class()
        self.user = User.objects.create_user(
            email="test@test.com",
            password="1234",
            birthday="2000-01-01",
            name="테스트유저",
            nickname="tester",
            phone_number="01000000001",
        )
        # 다른 사용자 추가
        self.other_user = User.objects.create_user(
            email="other@test.com",
            password="1234",
            birthday="2001-01-01",
            name="다른유저",
            nickname="other",
            phone_number="01000000002",
        )
        self.study_group = StudyGroup.objects.create(
            name="테스트 그룹",
            introduction="소개",
            max_headcount=5,
            start_at=timezone.now() - timedelta(days=10),
            end_at=timezone.now() - timedelta(days=1),
            status=StudyGroup.StatusChoices.ENDED,
        )
        self.review = StudyReview.objects.create(
            study_group=self.study_group,
            user=self.user,
            star_rating=5,
            content="테스트 리뷰",
        )
        self.url = f"/api/v1/study-groups/{self.study_group.uuid}/reviews/{self.review.id}"

    def test_update_review_success(self) -> None:
        """본인 리뷰 수정 성공"""
        self.client.force_authenticate(user=self.user)
        payload = {"star_rating": 4, "content": "시간이 부족했어요."}
        resp = self.client.patch(self.url, payload, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["user_uuid"], str(self.user.uuid))
        self.assertEqual(resp.data["study_group_uuid"], str(self.study_group.uuid))
        self.assertEqual(resp.data["star_rating"], 4)
        self.assertEqual(resp.data["content"], "시간이 부족했어요.")

    def test_update_review_fail_not_author(self) -> None:
        """작성자가 아닌 경우 403"""
        self.client.force_authenticate(user=self.other_user)
        payload = {"star_rating": 1}
        resp = self.client.patch(self.url, payload, format="json")

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", resp.data)
        self.assertEqual(resp.data["error"], "본인이 작성한 리뷰만 수정할 수 있습니다.")

    def test_update_review_fail_unauthenticated(self) -> None:
        """비로그인 사용자는 401"""
        payload = {"star_rating": 2}
        resp = self.client.patch(self.url, payload, format="json")

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
