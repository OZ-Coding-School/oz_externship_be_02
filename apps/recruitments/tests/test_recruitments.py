from rest_framework import status
from rest_framework.test import APITestCase


class RecruitmentDetailViewMockTest(APITestCase):
    def test_get_recruitment_detail_mock_success(self) -> None:
        # GIVEN: 테스트용 recruitmentId와 요청 URL 기초설정
        recruitment_id = 1
        url = f"/api/v1/recruitments/{recruitment_id}/"

        # WHEN: Mock API에 GET 요청보내기
        response = self.client.get(url)

        # THEN:
        # 1. 응답상태가 200 OK인지 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. 응답 데이터의 필드 존재여부 확인
        data = response.data
        self.assertEqual(data["id"], recruitment_id)
        self.assertIn("uuid", data)
        self.assertIn("author", data)
        self.assertIn("title", data)
        self.assertIn("content", data)
        self.assertIn("attachments", data)
        self.assertIn("expected_headcount", data)
        self.assertIn("estimated_fee", data)
        self.assertIn("lectures", data)
        self.assertIn("tags", data)
        self.assertIn("deadline", data)
        self.assertIn("created_at", data)
        self.assertIn("view_count", data)
        self.assertIn("bookmark_count", data)

        # 3. 중첩된 데이터의 구체적인 값이 명세와 일치 여부 확인
        self.assertEqual(data["author"]["nickname"], "해파리볶음밥")
        self.assertEqual(data["tags"][0]["name"], "#Django")
        self.assertEqual(data["attachments"][0]["file_name"], "study_plan_mock.pdf")
        self.assertEqual(data["lectures"][0]["instructor"], "최재현")
