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


class TestRunCrawlerV2Task(TestCase):
    @patch("apps.lectures.tasks.call_command")
    def test_task_calls_crawler_command(self, mock_call_command: MagicMock) -> None:
        run_crawler_v2()
        mock_call_command.assert_called_once_with("crawler_v2")

    @patch("apps.lectures.tasks.call_command")
    def test_task_runs_command_with_stdout(self, mock_call_command: MagicMock) -> None:
        mock_call_command.return_value = None
        run_crawler_v2()
        mock_call_command.assert_called_once_with("crawler_v2")


class TestCrawlerV2ErrorLogging(IsolatedAsyncioTestCase):
    @patch("apps.lectures.management.commands.crawler_v2.logger")
    async def test_page_crawling_error_logged(self, mock_logger: MagicMock) -> None:
        cmd: Command = Command()

        async def fake_fetch_page(client: Any, url: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
            if params.get("pageNumber") == 2:
                raise ValueError("테스트 오류")
            return [
                {
                    "course": {
                        "id": params.get("pageNumber"),
                        "title": f"강의 {params.get('pageNumber')}",
                        "slug": f"slug-{params.get('pageNumber')}",
                        "thumbnailUrl": "https://example.com/image.png",
                        "runtimeSecond": 3600,
                        "star": 4.5,
                        "description": "테스트 강의",
                        "metadata": {"level": "초급", "categories": [{"title": "테스트"}]},
                    },
                    "instructor": {"name": "강사"},
                    "listPrice": {"regularPrice": 100000, "payPrice": 50000},
                }
            ]

        with patch.object(cmd, "_fetch_page", side_effect=fake_fetch_page):
            await cmd._get_all_processed_data_from_api()

        found: bool = any(
            "페이지 크롤링 중 오류 발생: 테스트 오류" in str(call.args[0])
            for call in mock_logger.warning.call_args_list
        )
        assert found, "페이지 크롤링 중 오류 발생 로그가 호출되지 않음"

        async def fake_fetch_reviews(client: Any, course_id: int) -> List[Dict[str, Any]]:
            if course_id == 1:
                raise ValueError("리뷰 테스트 오류")
            return [{"course_id": course_id, "reviews": [{"rating": "5_OUT_OF_5_STARS", "content": "좋아요"}]}]

        with (
            patch.object(cmd, "_fetch_page", side_effect=fake_fetch_page),
            patch.object(cmd, "_fetch_reviews", side_effect=fake_fetch_reviews),
        ):
            await cmd._get_all_processed_data_from_api()

        found = any(
            isinstance(call.args[0], str)
            and "리뷰 크롤링 중 오류 발생" in call.args[0]
            and "리뷰 테스트 오류" in call.args[0]
            for call in mock_logger.warning.call_args_list
        )
        assert found, "리뷰 크롤링 중 오류 발생 로그가 호출되지 않음 또는 예외가 포함되지 않음"

    async def test_fetch_page_http_status_error_logged(self) -> None:
        cmd: Command = Command()
        mock_client: AsyncMock = AsyncMock()
        response_mock: AsyncMock = AsyncMock()
        response_mock.status_code = 404
        exc: httpx.HTTPStatusError = httpx.HTTPStatusError("Not Found", request=AsyncMock(), response=response_mock)
        mock_client.get.side_effect = exc

        with patch("apps.lectures.management.commands.crawler_v2.logger") as mock_logger:
            result: List[Dict[str, Any]] = await cmd._fetch_page(mock_client, "https://example.com", {"pageNumber": 1})

        assert result == []
        mock_logger.error.assert_any_call("페이지 1 로드 실패: 404")

    async def test_fetch_page_general_exception_logged(self) -> None:
        cmd: Command = Command()
        mock_client: AsyncMock = AsyncMock()
        mock_client.get.side_effect = ValueError("테스트 예외")

        with patch("apps.lectures.management.commands.crawler_v2.logger") as mock_logger:
            result: List[Dict[str, Any]] = await cmd._fetch_page(mock_client, "https://example.com", {"pageNumber": 2})

        assert result == []
        mock_logger.error.assert_any_call("페이지 2 처리 중 예외 발생: 테스트 예외")
