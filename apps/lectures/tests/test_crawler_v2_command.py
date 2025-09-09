import json
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now

from apps.lectures.models import Category, Lecture, LectureReview
from apps.lectures.models.crawled_lectures import PlatformChoices


class SyncInflearnV2CommandTest(TestCase):
    """
    crawler_v2 커맨드 테스트
    """

    def setUp(self) -> None:
        """테스트 시작 전, DB에 동기화 기준이 될 초기 데이터를 생성합니다."""
        # API 응답에 없고 DB에만 존재하는 강의 (삭제 대상)
        self.lecture_to_be_deleted = Lecture.objects.create(
            title="삭제될 강의",
            instructor="테스트 강사",
            platform=PlatformChoices.INFLEARN,
            url_link="http://test.com/deleted",
            duration=0,  # 필수 필드 값 추가
        )

        # API 응답과 DB에 모두 존재하는 강의 (유지 대상)
        self.lecture_to_be_kept = Lecture.objects.create(
            title="유지될 강의",
            instructor="기존 강사",
            platform=PlatformChoices.INFLEARN,
            url_link="http://test.com/kept",
            duration=0,  # 필수 필드 값 추가
        )

    def _mock_requests_get(self, *args: Any, **kwargs: Any) -> MagicMock:
        """URL에 따라 다른 Mock Response를 반환하는 함수"""
        url = args[0]
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        if "course/search" in url:
            # 강의 목록 API 응답
            mock_response.json.return_value = {
                "data": {
                    "totalPage": 1,
                    "items": [
                        {
                            "course": {
                                "id": 123,
                                "title": "새로운 V2 강의",
                                "slug": "new-v2-lecture",
                                "star": 4.8,
                                "runtimeSecond": 3600,
                                "description": "새로운 V2 강의 설명입니다.",
                                "thumbnailUrl": "http://test.com/thumb_v2.jpg",
                                "metadata": {
                                    "level": "초급",
                                    "categories": [{"title": "프로그래밍"}, {"title": "웹 개발"}],
                                },
                            },
                            "instructor": {"name": "신규 V2 강사"},
                            "listPrice": {"regularPrice": 100000, "payPrice": 50000},
                        },
                        {
                            "course": {
                                "id": 456,
                                "title": "유지될 강의",
                                "slug": "kept-lecture",
                                "star": 4.5,
                                "runtimeSecond": 7200,
                                "description": "유지될 강의 설명입니다.",
                                "thumbnailUrl": "http://test.com/thumb2.jpg",
                                "metadata": {"level": "중급", "categories": [{"title": "데이터 분석"}]},
                            },
                            "instructor": {"name": "기존 강사"},
                            "listPrice": {"regularPrice": 120000, "payPrice": 60000},
                        },
                    ],
                }
            }
        elif "reviews/course/123" in url:
            # '새로운 V2 강의'의 리뷰 API 응답
            mock_response.json.return_value = {
                "data": {
                    "items": [
                        {"star": 5, "body": "정말 최고의 V2 강의입니다!"},
                        {"star": 4, "body": "V2 들을만 합니다."},
                    ]
                }
            }
        elif "reviews/course/456" in url:
            # '유지될 강의'의 리뷰 API 응답 (리뷰가 없는 경우)
            mock_response.json.return_value = {"data": {"items": []}}
        else:
            # 예상치 못한 URL 호출 시 빈 응답 반환
            mock_response.json.return_value = {"data": {"items": []}}

        return mock_response

    @patch("requests.get")
    def test_crawler_v2_command_success(self, mock_get: MagicMock) -> None:
        """crawler_v2 커맨드 실행 시 데이터 동기화가 성공적으로 수행되는지 테스트"""
        # given
        mock_get.side_effect = self._mock_requests_get

        # when
        call_command("crawler_v2")

        # then
        # 1. 강의 개수 확인 (삭제 1, 유지 1, 추가 1 -> 총 2개)
        self.assertEqual(Lecture.objects.count(), 2)

        # 2. 강의가 정상적으로 삭제되었는지 확인
        self.assertFalse(Lecture.objects.filter(pk=self.lecture_to_be_deleted.pk).exists())

        # 3. 새로운 강의가 정상적으로 추가되었는지 확인
        self.assertTrue(Lecture.objects.filter(title="새로운 V2 강의").exists())
        new_lecture = Lecture.objects.get(title="새로운 V2 강의")
        self.assertEqual(new_lecture.instructor, "신규 V2 강사")
        self.assertEqual(new_lecture.average_rating, Decimal("4.8"))
        self.assertEqual(new_lecture.duration, 60)  # 3600초 -> 60분
        self.assertEqual(new_lecture.difficulty, "easy")
        self.assertEqual(new_lecture.original_price, 100000)
        self.assertEqual(new_lecture.discount_price, 50000)
        self.assertEqual(new_lecture.platform, PlatformChoices.INFLEARN)

        # 4. 카테고리가 생성되고 강의에 연결되었는지 확인
        self.assertEqual(Category.objects.count(), 2)  # 프로그래밍, 웹 개발
        self.assertEqual(new_lecture.categories.count(), 2)
        self.assertTrue(new_lecture.categories.filter(name="프로그래밍").exists())
        self.assertTrue(new_lecture.categories.filter(name="웹 개발").exists())

        # 5. 리뷰가 생성되고 강의에 연결되었는지 확인
        self.assertEqual(LectureReview.objects.count(), 2)
        self.assertEqual(new_lecture.reviews.count(), 2)
        self.assertTrue(new_lecture.reviews.filter(rating="5_OUT_OF_5_STARS").exists())
        review = new_lecture.reviews.get(rating="5_OUT_OF_5_STARS")
        self.assertEqual(review.content, "정말 최고의 V2 강의입니다!")

        # 6. 기존 강의가 유지되었는지 확인
        self.assertTrue(Lecture.objects.filter(pk=self.lecture_to_be_kept.pk).exists())
