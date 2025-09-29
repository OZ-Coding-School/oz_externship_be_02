import asyncio
import time
from typing import Any, Dict, List, Set, Tuple, Union, cast
from urllib.parse import quote

import httpx
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.logger import logger
from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lecture_reviews import LectureReview
from apps.lectures.models.crawled_lectures import Lecture, PlatformChoices


class Command(BaseCommand):
    """
    Inflearn의 강의 정보를 비동기적으로 크롤링하고 데이터베이스와 효율적으로 동기화하는 Django 관리자 명령어입니다.

    주요 기능:
    1. httpx와 asyncio를 사용하여 Inflearn API에서 강의 및 리뷰 정보를 병렬로 가져옵니다.
    2. 크롤링한 데이터를 바탕으로 로컬 데이터베이스와 비교하여 추가, 삭제할 강의를 결정합니다.
    3. Django ORM의 bulk_create를 사용하여 데이터베이스에 대량으로 데이터를 삽입하여 N+1 쿼리 문제를 해결했습니다
    """

    # --- 크롤링 설정 ---
    BASE_URL = "https://course-api.inflearn.com/client/api/v1/course/search"
    REVIEW_API_URL = "https://ucc-api.inflearn.com/client/api/v1/reviews/course/{course_id}"
    PAGE_SIZE = 100
    MAX_CONCURRENT_REQUESTS = 10

    def handle(self, *args: Any, **options: Any) -> None:
        asyncio.run(self._main())

    async def _main(self) -> None:
        """비동기 크롤링 및 동기화 프로세스를 총괄합니다."""
        logger.info("인프런 API 크롤링 및 DB 동기화를 시작합니다...")
        start_time = time.time()

        processed_courses_data = await self._get_all_processed_data_from_api()

        if not processed_courses_data:
            logger.warning("API로부터 가져올 강의 데이터가 없습니다.")
            return

        await sync_to_async(self.sync_data_with_db, thread_sensitive=True)(processed_courses_data)

        end_time = time.time()
        logger.info(f"총 실행 시간: {end_time - start_time:.2f}초")

    async def _get_all_processed_data_from_api(self) -> List[Dict[str, Any]]:
        """Inflearn API에서 모든 강의와 관련 리뷰를 비동기적으로 크롤링하여 가공합니다."""
        async with httpx.AsyncClient(timeout=20.0) as client:
            total_page = await self._get_total_pages(client)
            if total_page == 0:
                return []

            all_courses_raw = await self._fetch_all_courses_raw(client, total_page)
            course_id_map = {
                item.get("course", {}).get("id"): item for item in all_courses_raw if item.get("course", {}).get("id")
            }

            all_reviews_map = await self._fetch_all_reviews_map(client, list(course_id_map.keys()))

            return self._process_and_combine_data(course_id_map, all_reviews_map)

    async def _get_total_pages(self, client: httpx.AsyncClient) -> int:
        """API에서 전체 페이지 수를 가져옵니다."""
        params: Dict[str, Union[str, int]] = {
            "pageNumber": 1,
            "pageSize": self.PAGE_SIZE,
            "sort": "POPULAR",
            "lang": "ko",
        }
        try:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            total_page = cast(int, response.json().get("data", {}).get("totalPage", 1))
            logger.info(f"전체 페이지 수: {total_page}, 페이지 당 강의 수: {self.PAGE_SIZE}")
            return total_page
        except httpx.RequestError as e:
            logger.error(f"첫 페이지 요청 실패: {e}")
            return 0

    async def _fetch_all_courses_raw(self, client: httpx.AsyncClient, total_page: int) -> List[Dict[str, Any]]:
        """모든 페이지의 강의 목록을 병렬로 가져옵니다."""
        params: Dict[str, Union[str, int]] = {"pageSize": self.PAGE_SIZE, "sort": "POPULAR", "lang": "ko"}
        course_tasks = [
            self._fetch_page(client, self.BASE_URL, {**params, "pageNumber": page_num})
            for page_num in range(1, total_page + 1)
        ]

        all_courses_raw = []
        for i in range(0, len(course_tasks), self.MAX_CONCURRENT_REQUESTS):
            batch = course_tasks[i : i + self.MAX_CONCURRENT_REQUESTS]
            results = await asyncio.gather(*batch, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    all_courses_raw.extend(res)
                elif isinstance(res, Exception):
                    logger.warning(f"페이지 크롤링 중 오류 발생: {res}")
        return all_courses_raw

    async def _fetch_all_reviews_map(
        self, client: httpx.AsyncClient, course_ids: List[int]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """모든 강의의 리뷰를 병렬로 가져옵니다."""
        review_tasks = [self._fetch_reviews(client, course_id) for course_id in course_ids]

        all_reviews_map = {}
        for i in range(0, len(review_tasks), self.MAX_CONCURRENT_REQUESTS):
            batch = review_tasks[i : i + self.MAX_CONCURRENT_REQUESTS]
            results = await asyncio.gather(*batch, return_exceptions=True)
            for res in results:
                if isinstance(res, dict) and "course_id" in res:
                    all_reviews_map[res["course_id"]] = res["reviews"]
                elif isinstance(res, Exception):
                    logger.warning(f"리뷰 크롤링 중 오류 발생: {res}")
        return all_reviews_map

    def _process_and_combine_data(
        self,
        course_id_map: Dict[int, Dict[str, Any]],
        all_reviews_map: Dict[int, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """크롤링된 강의 데이터와 리뷰 데이터를 최종적인 형식으로 조합합니다."""
        all_processed_courses = []
        for course_id, item in course_id_map.items():
            course_info = item.get("course", {})
            processed_course = {
                "title": course_info.get("title"),
                "instructor": item.get("instructor", {}).get("name"),
                "average_rating": course_info.get("star", 0.0),
                "duration": course_info.get("runtimeSecond", 0) // 60,
                "difficulty": {"초급": "easy", "중급": "normal", "고급": "hard"}.get(
                    course_info.get("metadata", {}).get("level"), "easy"
                ),
                "description": course_info.get("description", "").replace("\n", " "),
                "platform": PlatformChoices.INFLEARN,
                "original_price": item.get("listPrice", {}).get("regularPrice", 0),
                "discount_price": item.get("listPrice", {}).get("payPrice", 0),
                "url_link": f"https://www.inflearn.com/course/{course_info.get('slug')}",
                "thumbnail_img_url": quote(course_info.get("thumbnailUrl"), safe=":/?&"),
                "categories": [
                    cat.get("title")
                    for cat in course_info.get("metadata", {}).get("categories", [])
                    if cat.get("title")
                ],
                "lecture_reviews": all_reviews_map.get(course_id, []),
            }
            all_processed_courses.append(processed_course)
        return all_processed_courses

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Dict[str, Union[str, int]],
    ) -> List[Dict[str, Any]]:
        """특정 페이지의 강의 목록을 비동기적으로 가져옵니다."""
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return cast(List[Dict[str, Any]], response.json().get("data", {}).get("items", []))
        except httpx.HTTPStatusError as e:
            logger.error(f"페이지 {params.get('pageNumber')} 로드 실패: {e.response.status_code}")
        except Exception as e:
            logger.error(f"페이지 {params.get('pageNumber')} 처리 중 예외 발생: {e}")
        return []

    async def _fetch_reviews(self, client: httpx.AsyncClient, course_id: int) -> Dict[str, Any]:
        """특정 강의의 리뷰를 비동기적으로 가져옵니다."""
        params: Dict[str, Union[str, int]] = {"pageNumber": 1, "pageSize": 4, "sort": "RECOMMEND", "lang": "ko"}
        rating_map = {
            5: "5_OUT_OF_5_STARS",
            4: "4_OUT_OF_5_STARS",
            3: "3_OUT_OF_5_STARS",
            2: "2_OUT_OF_5_STARS",
            1: "1_OUT_OF_5_STARS",
        }
        try:
            response = await client.get(self.REVIEW_API_URL.format(course_id=course_id), params=params)
            response.raise_for_status()
            processed_reviews = [
                {"rating": rating_map[review["star"]], "content": review.get("body", "")}
                for review in response.json().get("data", {}).get("items", [])
                if (rating := rating_map.get(review.get("star")))
            ]
            return {"course_id": course_id, "reviews": processed_reviews}
        except Exception:
            return {"course_id": course_id, "reviews": []}

    def sync_data_with_db(self, courses_data: List[Dict[str, Any]]) -> None:
        """크롤링된 데이터를 데이터베이스와 동기화합니다."""
        api_data_map, titles_to_add, titles_to_delete = self._prepare_sync_data(courses_data)

        reviews_to_create_len = 0
        if titles_to_delete:
            self._delete_lectures(titles_to_delete)

        if titles_to_add:
            reviews_to_create_len = self._create_new_data(titles_to_add, api_data_map)

        logger.info(
            f"동기화 완료! "
            f"신규 강의 {len(titles_to_add)}개, "
            f"삭제된 강의 {len(titles_to_delete)}개, "
            f"신규 리뷰 {reviews_to_create_len}개."
        )
        logger.info(
            f"DB에 이미 존재하여 건너뛴 강의 수: {len(api_data_map.keys() & set(Lecture.objects.filter(platform=PlatformChoices.INFLEARN).values_list('title', flat=True)))}개"
        )

    def _prepare_sync_data(
        self,
        courses_data: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Dict[str, Any]], Set[str], Set[str]]:
        """API 데이터와 로컬 DB 데이터를 비교하여 동기화할 데이터를 준비합니다."""
        api_data_map = {item["title"]: item for item in courses_data if item.get("title")}
        api_titles = set(api_data_map.keys())
        local_titles = set(Lecture.objects.filter(platform=PlatformChoices.INFLEARN).values_list("title", flat=True))

        titles_to_add = api_titles - local_titles
        titles_to_delete = local_titles - api_titles

        return api_data_map, titles_to_add, titles_to_delete

    def _delete_lectures(self, titles_to_delete: Set[str]) -> None:
        """DB에서 삭제할 강의를 제거합니다."""
        deleted_count, _ = Lecture.objects.filter(
            platform=PlatformChoices.INFLEARN, title__in=titles_to_delete
        ).delete()
        logger.info(f"삭제된 강의 수: {deleted_count}개")

    def _create_new_data(self, titles_to_add: Set[str], api_data_map: Dict[str, Dict[str, Any]]) -> int:
        """신규 강의, 카테고리, 리뷰 데이터를 DB에 생성합니다."""
        lectures_to_create, lecture_category_map = self._prepare_lectures_for_creation(titles_to_add, api_data_map)

        reviews_to_create_len = 0
        with transaction.atomic():
            if not lectures_to_create:
                return 0

            created_lectures_map = self._bulk_create_lectures(lectures_to_create, titles_to_add)
            if not created_lectures_map:
                return 0

            existing_cats = self._handle_categories(lecture_category_map)

            lecture_category_relations, reviews_to_create = self._prepare_relations_and_reviews(
                created_lectures_map, lecture_category_map, existing_cats, api_data_map
            )

            self._bulk_create_relations_and_reviews(lecture_category_relations, reviews_to_create)
            reviews_to_create_len = len(reviews_to_create)
        return reviews_to_create_len

    def _prepare_lectures_for_creation(
        self,
        titles_to_add: Set[str],
        api_data_map: Dict[str, Dict[str, Any]],
    ) -> Tuple[List[Lecture], Dict[str, List[str]]]:
        """생성할 강의 객체와 강의-카테고리 맵을 준비합니다."""
        lectures_to_create = []
        lecture_category_map = {}
        for title in titles_to_add:
            item = api_data_map[title]
            lectures_to_create.append(
                Lecture(
                    title=item.get("title") or "",
                    instructor=item.get("instructor") or "",
                    average_rating=item.get("average_rating", 0.0),
                    duration=item.get("duration", 0),
                    difficulty=item.get("difficulty", "easy"),
                    description=item.get("description", ""),
                    platform=PlatformChoices.INFLEARN,
                    original_price=item.get("original_price", 0),
                    discount_price=item.get("discount_price", 0),
                    url_link=item.get("url_link") or "",
                    thumbnail_img_url=item.get("thumbnail_img_url") or "",
                )
            )
            lecture_category_map[title] = item.get("categories", [])
        return lectures_to_create, lecture_category_map

    def _bulk_create_lectures(self, lectures_to_create: List[Lecture], titles_to_add: Set[str]) -> Dict[str, Lecture]:
        """신규 강의를 bulk_create로 삽입하고, 생성된 객체를 맵으로 반환합니다."""
        Lecture.objects.bulk_create(lectures_to_create, ignore_conflicts=True)
        logger.info(f"신규 강의 {len(lectures_to_create)}개 생성 시도 완료.")

        created_lectures_map = {lec.title: lec for lec in Lecture.objects.filter(title__in=titles_to_add)}
        logger.info(f"DB에서 ID가 할당된 신규 강의 {len(created_lectures_map)}개 확인.")
        return created_lectures_map

    def _handle_categories(self, lecture_category_map: Dict[str, List[str]]) -> Dict[str, Category]:
        """카테고리를 조회하고, 신규 카테고리는 생성하여 전체 카테고리 맵을 반환합니다."""
        all_cat_names = {cat for cats in lecture_category_map.values() for cat in cats}
        existing_cats = {cat.name: cat for cat in Category.objects.filter(name__in=all_cat_names)}
        new_cat_names = all_cat_names - set(existing_cats.keys())
        if new_cat_names:
            new_cats = Category.objects.bulk_create([Category(name=name) for name in new_cat_names])
            for cat in new_cats:
                existing_cats[cat.name] = cat
        return existing_cats

    def _prepare_relations_and_reviews(
        self,
        created_lectures_map: Dict[str, Lecture],
        lecture_category_map: Dict[str, List[str]],
        existing_cats: Dict[str, Category],
        api_data_map: Dict[str, Dict[str, Any]],
    ) -> Tuple[List[Any], List[LectureReview]]:
        """강의-카테고리 관계와 리뷰 데이터를 생성 준비합니다."""
        LectureCategoryThrough = Lecture.categories.through
        lecture_category_relations = []
        reviews_to_create = []

        for title, lecture in created_lectures_map.items():
            cat_names = lecture_category_map.get(title, [])
            for cat_name in cat_names:
                if category := existing_cats.get(cat_name):
                    lecture_category_relations.append(
                        LectureCategoryThrough(lecture_id=lecture.id, category_id=category.id)
                    )

            reviews_data = api_data_map[title].get("lecture_reviews", [])
            for review_data in reviews_data:
                reviews_to_create.append(
                    LectureReview(lecture=lecture, rating=review_data["rating"], content=review_data["content"])
                )
        return lecture_category_relations, reviews_to_create

    def _bulk_create_relations_and_reviews(
        self,
        lecture_category_relations: List[Any],
        reviews_to_create: List[LectureReview],
    ) -> None:
        """준비된 관계 및 리뷰 데이터를 bulk_create로 삽입합니다."""
        if lecture_category_relations:
            Lecture.categories.through.objects.bulk_create(lecture_category_relations, ignore_conflicts=True)
        if reviews_to_create:
            LectureReview.objects.bulk_create(reviews_to_create, ignore_conflicts=True)
            logger.info(f"신규 리뷰 {len(reviews_to_create)}개 생성 완료.")
