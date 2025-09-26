import asyncio
from io import StringIO
from typing import Any, Dict, List, Optional
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from django.core.management import call_command
from django.test import TestCase

from apps.lectures.management.commands.crawler_v2 import Command
from apps.lectures.models import Category, Lecture, LectureReview
from apps.lectures.tasks import run_crawler_v2


class TestCrawlerV2Command(IsolatedAsyncioTestCase):
    """
    crawler_v2 명령어 테스트 클래스
    """
    @patch("apps.lectures.management.commands.crawler_v2.logger")
    @patch("apps.lectures.management.commands.crawler_v2.httpx.AsyncClient")
    async def test_handle_success(self, mock_async_client: MagicMock, mock_logger: MagicMock) -> None:
        """
        명령어가 성공적으로 실행되는 경우를 테스트합니다.
        """
        mock_response_page1: MagicMock = MagicMock()
        mock_response_page1.json.return_value = {
            "data": {
                "totalPage": 1,
                "items": [
                    {
                        "course": {
                            "id": 1,
                            "title": "Test Lecture 1",
                            "star": 4.5,
                            "runtimeSecond": 3600,
                            "metadata": {"level": "초급", "categories": [{"title": "Test Category 1"}]},
                            "description": "Test Description 1",
                            "slug": "test-lecture-1",
                            "thumbnailUrl": "http://example.com/thumb1.jpg",
                        },
                        "instructor": {"name": "Test Instructor 1"},
                        "listPrice": {"regularPrice": 10000, "payPrice": 8000},
                    }
                ],
            }
        }
        mock_response_page1.raise_for_status = MagicMock()

        mock_response_reviews: MagicMock = MagicMock()
        mock_response_reviews.json.return_value = {"data": {"items": [{"star": 5, "body": "Great lecture!"}]}}
        mock_response_reviews.raise_for_status = MagicMock()

        mock_get: AsyncMock = AsyncMock()
        mock_get.side_effect = [mock_response_page1, mock_response_page1, mock_response_reviews]

        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get = mock_get
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        out: StringIO = StringIO()
        await asyncio.to_thread(call_command, "crawler_v2", stdout=out, stderr=out)

        self.assertEqual(await Lecture.objects.acount(), 1)
        self.assertEqual(await Category.objects.acount(), 1)
        self.assertEqual(await LectureReview.objects.acount(), 1)

        lecture: Optional[Lecture] = await Lecture.objects.afirst()
        category: Optional[Category] = await Category.objects.afirst()
        review: Optional[LectureReview] = await LectureReview.objects.afirst()

        if lecture and category and review:
            self.assertEqual(lecture.title, "Test Lecture 1")
            self.assertEqual(lecture.instructor, "Test Instructor 1")
            self.assertEqual(lecture.platform, "inflearn")
            self.assertEqual(category.name, "Test Category 1")
            self.assertEqual(review.content, "Great lecture!")
            self.assertEqual(review.rating, "5_OUT_OF_5_STARS")

            lecture_categories: List[str] = [cat.name async for cat in lecture.categories.all()]
            self.assertIn("Test Category 1", lecture_categories)
        else:
            self.fail("lecture, category or review is None")

    @patch("apps.lectures.management.commands.crawler_v2.logger")
    @patch("apps.lectures.management.commands.crawler_v2.httpx.AsyncClient")
    async def test_sync_deletes_old_lectures(self, mock_async_client: MagicMock, mock_logger: MagicMock) -> None:
        """
        API에 더 이상 존재하지 않는 강의가 DB에서 삭제되는지 테스트합니다.
        """
        await Lecture.objects.acreate(
            title="Old Lecture", platform="inflearn", url_link="http://example.com/old", duration=0
        )

        mock_response_page1: MagicMock = MagicMock()
        mock_response_page1.json.return_value = {
            "data": {
                "totalPage": 1,
                "items": [
                    {
                        "course": {
                            "id": 1,
                            "title": "New Lecture",
                            "star": 4.5,
                            "runtimeSecond": 3600,
                            "metadata": {"level": "초급", "categories": [{"title": "New Category"}]},
                            "description": "New Description",
                            "slug": "new-lecture",
                            "thumbnailUrl": "http://example.com/thumb_new.jpg",
                        },
                        "instructor": {"name": "New Instructor"},
                        "listPrice": {"regularPrice": 10000, "payPrice": 8000},
                    }
                ],
            }
        }
        mock_response_page1.raise_for_status = MagicMock()

        mock_response_reviews: MagicMock = MagicMock()
        mock_response_reviews.json.return_value = {"data": {"items": []}}
        mock_response_reviews.raise_for_status = MagicMock()

        mock_get: AsyncMock = AsyncMock()
        mock_get.side_effect = [mock_response_page1, mock_response_page1, mock_response_reviews]

        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get = mock_get
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        out: StringIO = StringIO()
        await asyncio.to_thread(call_command, "crawler_v2", stdout=out, stderr=out)

        self.assertEqual(await Lecture.objects.acount(), 1)
        lecture_exists: bool = await Lecture.objects.filter(title="Old Lecture").aexists()
        self.assertFalse(lecture_exists)
        new_lecture_exists: bool = await Lecture.objects.filter(title="New Lecture").aexists()
        self.assertTrue(new_lecture_exists)

    @patch("apps.lectures.management.commands.crawler_v2.logger")
    @patch("apps.lectures.management.commands.crawler_v2.httpx.AsyncClient")
    async def test_handle_api_request_error(self, mock_async_client: MagicMock, mock_logger: MagicMock) -> None:
        """
        API 요청 실패 시 에러를 처리하는지 테스트합니다.
        """
        mock_get: AsyncMock = AsyncMock(side_effect=httpx.RequestError("API request failed"))
        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get = mock_get
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        out: StringIO = StringIO()
        await asyncio.to_thread(call_command, "crawler_v2", stdout=out, stderr=out)

        self.assertEqual(await Lecture.objects.acount(), 0)
        self.assertEqual(await Category.objects.acount(), 0)
        self.assertEqual(await LectureReview.objects.acount(), 0)
        mock_logger.error.assert_called_with("첫 페이지 요청 실패: API request failed")

    @patch("apps.lectures.management.commands.crawler_v2.logger")
    @patch("apps.lectures.management.commands.crawler_v2.httpx.AsyncClient")
    async def test_handle_no_data_from_api(self, mock_async_client: MagicMock, mock_logger: MagicMock) -> None:
        """
        API에서 가져올 데이터가 없을 경우를 테스트합니다.
        """
        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {"data": {"totalPage": 0, "items": []}}
        mock_response.raise_for_status = MagicMock()

        mock_get: AsyncMock = AsyncMock(return_value=mock_response)
        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get = mock_get
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        out: StringIO = StringIO()
        await asyncio.to_thread(call_command, "crawler_v2", stdout=out, stderr=out)

        self.assertEqual(await Lecture.objects.acount(), 0)
        mock_logger.warning.assert_called_with("API로부터 가져올 강의 데이터가 없습니다.")

