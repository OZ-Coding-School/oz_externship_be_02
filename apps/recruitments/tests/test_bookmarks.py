from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.lectures.models import Lecture
from apps.recruitments.models import Recruitment, RecruitmentBookmark
from apps.studies.models import StudyGroup
from apps.users.models import User


class BookmarkAPITestCase(APITestCase):
    def setUp(self) -> None:
        """테스트에 필요한 초기 데이터 설정"""
        self.user1 = User.objects.create_user(
            email="user1@test.com",
            password="password123",
            nickname="테스터1",
            name="김테스터",
            phone_number="010-1111-1111",
            gender="M",
            birthday=date(2000, 1, 1),
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com",
            password="password123",
            nickname="테스터2",
            name="이테스터",
            phone_number="010-2222-2222",
            gender="F",
            birthday=date(2000, 1, 1),
        )

        self.lecture1 = Lecture.objects.create(
            title="강의1",
            instructor="강사1",
            platform="플랫폼1",
            duration=100,
            difficulty="normal",
            description="테스트용 강의 설명",
            url_link="http://test.com/lecture1",
        )
        self.study_group1 = StudyGroup.objects.create(
            name="스터디그룹1",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )
        self.study_group1.lectures.add(self.lecture1)

        self.recruitment1 = Recruitment.objects.create(
            author=self.user1,
            study_group=self.study_group1,
            title="공고1",
            content="내용1",
            expected_headcount=5,
            estimated_fee=10000,
        )
        self.recruitment2 = Recruitment.objects.create(
            author=self.user1,
            study_group=self.study_group1,
            title="공고2",
            content="내용2",
            expected_headcount=5,
            estimated_fee=20000,
        )

    # --- REQ-RECM-010: 북마크 추가 테스트 --- #

    def test_add_bookmark_success(self) -> None:
        """인증된 사용자가 북마크 추가 시 201 응답 및 DB 레코드 확인"""
        self.client.force_authenticate(user=self.user2)
        url = reverse("recruitment-bookmark", kwargs={"recruitment_id": self.recruitment1.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RecruitmentBookmark.objects.filter(user=self.user2, recruitment=self.recruitment1).exists())

    def test_add_bookmark_unauthenticated(self) -> None:
        """인증되지 않은 사용자의 북마크 추가 요청 시 401 응답 확인"""
        url = reverse("recruitment-bookmark", kwargs={"recruitment_id": self.recruitment1.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_bookmark_already_exists(self) -> None:
        """이미 북마크한 공고에 재요청 시 200 응답 확인"""
        self.client.force_authenticate(user=self.user2)
        # 먼저 북마크를 추가
        RecruitmentBookmark.objects.create(user=self.user2, recruitment=self.recruitment1)

        url = reverse("recruitment-bookmark", kwargs={"recruitment_id": self.recruitment1.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RecruitmentBookmark.objects.filter(user=self.user2, recruitment=self.recruitment1).count(), 1)

    def test_add_bookmark_nonexistent_recruitment(self) -> None:
        """존재하지 않는 공고에 북마크 요청 시 404 응답 확인"""
        self.client.force_authenticate(user=self.user2)
        non_existent_id = 9999
        url = reverse("recruitment-bookmark", kwargs={"recruitment_id": non_existent_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- REQ-RECM-010: 북마크 삭제 테스트 --- #

    def test_remove_bookmark_success(self) -> None:
        """인증된 사용자가 북마크 삭제 시 204 응답 및 DB 레코드 삭제 확인"""
        self.client.force_authenticate(user=self.user2)
        # 먼저 북마크를 추가
        RecruitmentBookmark.objects.create(user=self.user2, recruitment=self.recruitment1)

        url = reverse("recruitment-bookmark", kwargs={"recruitment_id": self.recruitment1.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RecruitmentBookmark.objects.filter(user=self.user2, recruitment=self.recruitment1).exists())

    def test_remove_bookmark_not_bookmarked(self) -> None:
        """북마크하지 않은 공고에 삭제 요청 시 404 응답 확인"""
        self.client.force_authenticate(user=self.user2)
        url = reverse("recruitment-bookmark", kwargs={"recruitment_id": self.recruitment1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- REQ-RECM-011: 북마크 목록 조회 테스트 --- #

    def test_list_bookmarked_recruitments_success(self) -> None:
        """인증된 사용자가 자신의 북마크 목록을 정확히 받는지 확인"""
        self.client.force_authenticate(user=self.user2)
        # user2가 recruitment1, recruitment2를 북마크
        RecruitmentBookmark.objects.create(user=self.user2, recruitment=self.recruitment1)
        RecruitmentBookmark.objects.create(user=self.user2, recruitment=self.recruitment2)

        url = reverse("my-bookmark-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        # 최신순으로 정렬되므로 recruitment2가 먼저 나와야 함
        self.assertEqual(response.data["results"][0]["title"], "공고2")
        self.assertEqual(response.data["results"][1]["title"], "공고1")

    def test_list_bookmarked_recruitments_empty(self) -> None:
        """북마크가 없는 사용자의 경우 빈 목록이 반환되는지 확인"""
        self.client.force_authenticate(user=self.user2)
        url = reverse("my-bookmark-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_list_bookmarked_recruitments_unauthenticated(self) -> None:
        """인증되지 않은 사용자의 목록 조회 요청 시 401 응답 확인"""
        url = reverse("my-bookmark-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
