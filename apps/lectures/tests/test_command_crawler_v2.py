import asyncio
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from django.core.management import call_command
from django.test import TestCase

from apps.lectures.management.commands.crawler_v2 import Command
from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lecture_reviews import LectureReview
from apps.lectures.models.crawled_lectures import Lecture, PlatformChoices


class TestCrawlerV2CommandIntegration(TestCase):
    """
    crawler_v2 명령어 통합 테스트 클래스
    """

    @patch("apps.lectures.management.commands.crawler_v2.logger")
    @patch("apps.lectures.management.commands.crawler_v2.httpx.AsyncClient")
    async def test_handle_success(self, mock_async_client: MagicMock, mock_logger: MagicMock) -> None:
        """
        명령어가 성공적으로 실행되는 경우를 테스트합니다.
        """
        # given: Mocking a successful API response
        mock_response_page1 = MagicMock()
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

        mock_response_reviews = MagicMock()
        mock_response_reviews.json.return_value = {
            "data": {
                "items": [
                    {"star": 5, "body": "Great lecture!"},
                ]
            }
        }
        mock_response_reviews.raise_for_status = MagicMock()

        mock_get = AsyncMock()
        mock_get.side_effect = [
            mock_response_page1,  # First call for total pages
            mock_response_page1,  # Call for page 1
            mock_response_reviews,  # Call for reviews
        ]

        mock_client_instance = MagicMock()
        mock_client_instance.get = mock_get
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # when: Running the command
        out = StringIO()
        await asyncio.to_thread(call_command, "crawler_v2", stdout=out, stderr=out)

        # then: Verifying the database state
        self.assertEqual(await Lecture.objects.acount(), 1)
        self.assertEqual(await Category.objects.acount(), 1)
        self.assertEqual(await LectureReview.objects.acount(), 1)

        lecture = await Lecture.objects.afirst()
        category = await Category.objects.afirst()
        review = await LectureReview.objects.afirst()

        if lecture and category and review:
            self.assertEqual(lecture.title, "Test Lecture 1")
            self.assertEqual(lecture.instructor, "Test Instructor 1")
            self.assertEqual(lecture.platform, "inflearn")
            self.assertEqual(category.name, "Test Category 1")
            self.assertEqual(review.content, "Great lecture!")
            self.assertEqual(review.rating, "5_OUT_OF_5_STARS")

            # Check M2M relationship
            lecture_categories = [cat.name async for cat in lecture.categories.all()]
            self.assertIn("Test Category 1", lecture_categories)
        else:
            self.fail("lecture, category or review is None")

    @patch("apps.lectures.management.commands.crawler_v2.logger")
    @patch("apps.lectures.management.commands.crawler_v2.httpx.AsyncClient")
    async def test_sync_deletes_old_lectures(self, mock_async_client: MagicMock, mock_logger: MagicMock) -> None:
        """
        API에 더 이상 존재하지 않는 강의가 DB에서 삭제되는지 테스트합니다.
        """
        # given: An existing lecture in the DB
        await Lecture.objects.acreate(
            title="Old Lecture", platform="inflearn", url_link="http://example.com/old", duration=0
        )

        # Mocking an API response that does not contain the old lecture
        mock_response_page1 = MagicMock()
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

        mock_response_reviews = MagicMock()
        mock_response_reviews.json.return_value = {"data": {"items": []}}
        mock_response_reviews.raise_for_status = MagicMock()

        mock_get = AsyncMock()
        mock_get.side_effect = [
            mock_response_page1,
            mock_response_page1,
            mock_response_reviews,
        ]

        mock_client_instance = MagicMock()
        mock_client_instance.get = mock_get
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # when: Running the command
        out = StringIO()
        await asyncio.to_thread(call_command, "crawler_v2", stdout=out, stderr=out)

        # then: Verifying the old lecture is deleted and the new one is added
        self.assertEqual(await Lecture.objects.acount(), 1)
        lecture_exists = await Lecture.objects.filter(title="Old Lecture").aexists()
        self.assertFalse(lecture_exists)
        new_lecture_exists = await Lecture.objects.filter(title="New Lecture").aexists()
        self.assertTrue(new_lecture_exists)

    @patch("apps.lectures.management.commands.crawler_v2.logger")
    @patch("apps.lectures.management.commands.crawler_v2.httpx.AsyncClient")
    async def test_handle_api_request_error(self, mock_async_client: MagicMock, mock_logger: MagicMock) -> None:
        """
        API 요청 실패 시 에러를 처리하는지 테스트합니다.
        """
        # given: Mocking a request error
        mock_get = AsyncMock(side_effect=httpx.RequestError("API request failed"))
        mock_client_instance = MagicMock()
        mock_client_instance.get = mock_get
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # when: Running the command
        out = StringIO()
        await asyncio.to_thread(call_command, "crawler_v2", stdout=out, stderr=out)

        # then: Verifying no data is created and the process finishes gracefully
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
        # given: Mocking an empty API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"totalPage": 0, "items": []}}
        mock_response.raise_for_status = MagicMock()

        mock_get = AsyncMock(return_value=mock_response)
        mock_client_instance = MagicMock()
        mock_client_instance.get = mock_get
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # when: Running the command
        out = StringIO()
        await asyncio.to_thread(call_command, "crawler_v2", stdout=out, stderr=out)

        # then: Verifying no data is created and a warning is logged
        self.assertEqual(await Lecture.objects.acount(), 0)
        mock_logger.warning.assert_called_with("API로부터 가져올 강의 데이터가 없습니다.")


class TestCrawlerV2CommandUnit(TestCase):
    def setUp(self) -> None:
        self.command = Command()

    async def test_get_total_pages_success(self) -> None:
        """_get_total_pages가 성공적으로 페이지 수를 반환하는지 테스트합니다."""
        # given
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"totalPage": 10}}
        mock_client.get.return_value = mock_response

        # when
        total_pages = await self.command._get_total_pages(mock_client)

        # then
        self.assertEqual(total_pages, 10)
        mock_client.get.assert_called_once()

    async def test_get_total_pages_failure(self) -> None:
        """_get_total_pages가 API 요청 실패 시 0을 반환하는지 테스트합니다."""
        # given
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.RequestError("API down")

        # when
        total_pages = await self.command._get_total_pages(mock_client)

        # then
        self.assertEqual(total_pages, 0)

    def test_process_and_combine_data(self) -> None:
        """_process_and_combine_data가 데이터를 올바르게 가공하고 조합하는지 테스트합니다."""
        # given
        course_id_map = {
            1: {
                "course": {
                    "id": 1,
                    "title": "Test Course",
                    "star": 4.5,
                    "runtimeSecond": 3600,
                    "metadata": {"level": "초급", "categories": [{"title": "Dev"}]},
                    "description": "A test course.",
                    "slug": "test-course",
                    "thumbnailUrl": "http://example.com/thumb.jpg",
                },
                "instructor": {"name": "John Doe"},
                "listPrice": {"regularPrice": 100, "payPrice": 80},
            }
        }
        all_reviews_map = {1: [{"rating": "5_OUT_OF_5_STARS", "content": "Great!"}]}

        # when
        processed_data = self.command._process_and_combine_data(course_id_map, all_reviews_map)

        # then
        self.assertEqual(len(processed_data), 1)
        course = processed_data[0]
        self.assertEqual(course["title"], "Test Course")
        self.assertEqual(course["instructor"], "John Doe")
        self.assertEqual(course["average_rating"], 4.5)
        self.assertEqual(course["duration"], 60)
        self.assertEqual(course["difficulty"], "easy")
        self.assertEqual(course["platform"], PlatformChoices.INFLEARN)
        self.assertEqual(course["original_price"], 100)
        self.assertEqual(course["discount_price"], 80)
        self.assertIn("Dev", course["categories"])
        self.assertEqual(len(course["lecture_reviews"]), 1)
        self.assertEqual(course["lecture_reviews"][0]["content"], "Great!")

    @patch("apps.lectures.management.commands.crawler_v2.logger")
    def test_prepare_sync_data(self, mock_logger: MagicMock) -> None:
        """_prepare_sync_data가 동기화할 데이터를 정확히 준비하는지 테스트합니다."""
        # given
        courses_data = [
            {"title": "New Lecture 1"},
            {"title": "Existing Lecture"},
        ]
        Lecture.objects.create(title="Existing Lecture", platform=PlatformChoices.INFLEARN, url_link="", duration=0)
        Lecture.objects.create(title="Old Lecture", platform=PlatformChoices.INFLEARN, url_link="", duration=0)

        # when
        api_data_map, titles_to_add, titles_to_delete = self.command._prepare_sync_data(courses_data)

        # then
        self.assertIn("New Lecture 1", titles_to_add)
        self.assertNotIn("Existing Lecture", titles_to_add)
        self.assertIn("Old Lecture", titles_to_delete)
        self.assertIn("New Lecture 1", api_data_map)

    def test_delete_lectures(self) -> None:
        """_delete_lectures가 지정된 강의를 삭제하는지 테스트합니다."""
        # given
        Lecture.objects.create(title="Lecture to Delete", platform=PlatformChoices.INFLEARN, url_link="", duration=0)
        titles_to_delete = {"Lecture to Delete"}

        # when
        self.command._delete_lectures(titles_to_delete)

        # then
        self.assertFalse(Lecture.objects.filter(title="Lecture to Delete").exists())