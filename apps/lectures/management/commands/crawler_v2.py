import asyncio
import time
from typing import Any, Dict, List, Union
from urllib.parse import quote

import httpx
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.logger import logger
from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import Lecture, PlatformChoices
from apps.lectures.models.crawled_lecture_reviews import LectureReview


class Command(BaseCommand):
    help = "인프런 API에서 직접 데이터를 가져와 DB와 효율적으로 동기화합니다."

    BASE_URL = "https://course-api.inflearn.com/client/api/v1/course/search"
    REVIEW_API_URL = "https://ucc-api.inflearn.com/client/api/v1/reviews/course/{course_id}"
    PAGE_SIZE = 100
    MAX_CONCURRENT_REQUESTS = 10

    def handle(self, *args: Any, **options: Any) -> None:
        async def main() -> None:
            logger.info("인프런 API 크롤링 및 DB 동기화를 시작합니다...")
            start_time = time.time()

            processed_courses_data = await self._get_all_processed_data_from_api()

            if not processed_courses_data:
                logger.warning("API로부터 가져올 강의 데이터가 없습니다.")
            else:
                await sync_to_async(self.sync_data_with_db, thread_sensitive=True)(processed_courses_data)

            end_time = time.time()
            logger.info(f"총 실행 시간: {end_time - start_time:.2f}초")

        # 이미 이벤트 루프가 돌고 있는 환경에서는 asyncio.run 사용 불가
        try:
            asyncio.run(main())
        except RuntimeError:
            # 주피터/테스트 환경 등에서 이벤트 루프가 이미 돌고 있을 수 있음
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())

    async def _get_all_processed_data_from_api(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            params: Dict[str, Union[str, int]] = {
                "pageNumber": 1,
                "pageSize": self.PAGE_SIZE,
                "sort": "POPULAR",
                "lang": "ko",
            }
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                total_page = data.get("data", {}).get("totalPage", 1)
                logger.info(f"전체 페이지 수: {total_page}, 페이지 당 강의 수: {self.PAGE_SIZE}")
            except Exception as e:
                logger.error(f"첫 페이지 요청 실패: {e}")
                return []

            # 모든 페이지 크롤링
            course_tasks = [
                self._fetch_page(client, {**params, "pageNumber": page_num})
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

            # 리뷰 크롤링
            course_id_map = {item.get("course", {}).get("id"): item for item in all_courses_raw if item.get("course", {}).get("id")}
            review_tasks = [self._fetch_reviews(client, course_id) for course_id in course_id_map.keys()]

            all_reviews_map = {}
            for i in range(0, len(review_tasks), self.MAX_CONCURRENT_REQUESTS):
                batch = review_tasks[i : i + self.MAX_CONCURRENT_REQUESTS]
                results = await asyncio.gather(*batch, return_exceptions=True)
                for res in results:
                    if isinstance(res, list) and res:
                        review_dict = res[0]
                        if "course_id" in review_dict:
                            all_reviews_map[review_dict["course_id"]] = review_dict["reviews"]

            # 최종 데이터 조합
            processed_courses = []
            for course_id, item in course_id_map.items():
                course_info = item.get("course", {})
                processed_courses.append({
                    "title": course_info.get("title"),
                    "instructor": item.get("instructor", {}).get("name"),
                    "average_rating": course_info.get("star", 0.0),
                    "duration": course_info.get("runtimeSecond", 0) // 60 or 0,
                    "difficulty": {"초급": "easy", "중급": "normal", "고급": "hard"}.get(
                        course_info.get("metadata", {}).get("level"), "easy"
                    ),
                    "description": course_info.get("description", "").replace("\n", " "),
                    "platform": "Inflearn",
                    "original_price": item.get("listPrice", {}).get("regularPrice", 0),
                    "discount_price": item.get("listPrice", {}).get("payPrice", 0),
                    "url_link": f"https://www.inflearn.com/course/{course_info.get('slug')}",
                    "thumbnail_img_url": quote(course_info.get("thumbnailUrl") or "", safe=":/?&"),
                    "categories": [cat.get("title") for cat in course_info.get("metadata", {}).get("categories", []) if cat.get("title")],
                    "lecture_reviews": all_reviews_map.get(course_id, []),
                })
            return processed_courses

    async def _fetch_page(self, client: httpx.AsyncClient, params: Dict[str, Union[str, int]]) -> List[Dict[str, Any]]:
        try:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json().get("data", {}).get("items", [])
        except Exception as e:
            logger.error(f"페이지 {params.get('pageNumber')} 처리 중 예외 발생: {e}")
            return []

    async def _fetch_reviews(self, client: httpx.AsyncClient, course_id: int) -> List[Dict[str, Any]]:
        params = {"pageNumber": 1, "pageSize": 4, "sort": "RECOMMEND", "lang": "ko"}
        rating_map = {5: "5_OUT_OF_5_STARS", 4: "4_OUT_OF_5_STARS", 3: "3_OUT_OF_5_STARS", 2: "2_OUT_OF_5_STARS", 1: "1_OUT_OF_5_STARS"}
        try:
            response = await client.get(self.REVIEW_API_URL.format(course_id=course_id), params=params)
            response.raise_for_status()
            processed_reviews = [
                {"rating": rating_map.get(r.get("star")), "content": r.get("body", "")}
                for r in response.json().get("data", {}).get("items", [])
                if rating_map.get(r.get("star"))
            ]
            return [{"course_id": course_id, "reviews": processed_reviews}]
        except Exception:
            return []

    def sync_data_with_db(self, courses_data: List[Dict[str, Any]]) -> None:
        api_data_map = {item["title"]: item for item in courses_data if item.get("title")}
        api_titles = set(api_data_map.keys())
        local_titles = set(Lecture.objects.filter(platform=PlatformChoices.INFLEARN).values_list("title", flat=True))

        titles_to_add = api_titles - local_titles
        titles_to_delete = local_titles - api_titles

        if titles_to_delete:
            Lecture.objects.filter(platform=PlatformChoices.INFLEARN, title__in=titles_to_delete).delete()

        lectures_to_create = []
        lecture_category_map = {}
        for title in titles_to_add:
            item = api_data_map[title]
            lectures_to_create.append(
                Lecture(
                    title=item.get("title") or "",
                    instructor=item.get("instructor") or "",
                    average_rating=item.get("average_rating", 0.0),
                    duration=item.get("duration", 0) or 0,
                    difficulty=item.get("difficulty", "easy"),
                    description=item.get("description") or "",
                    platform=PlatformChoices.INFLEARN,
                    original_price=item.get("original_price", 0),
                    discount_price=item.get("discount_price", 0),
                    url_link=item.get("url_link") or "",
                    thumbnail_img_url=item.get("thumbnail_img_url") or "",
                )
            )
            lecture_category_map[title] = item.get("categories", [])

        reviews_to_create = []
        with transaction.atomic():
            if lectures_to_create:
                Lecture.objects.bulk_create(lectures_to_create, ignore_conflicts=True)
                created_lectures_map = {lec.title: lec for lec in Lecture.objects.filter(title__in=titles_to_add)}

                all_cat_names = {cat for cats in lecture_category_map.values() for cat in cats}
                existing_cats = {cat.name: cat for cat in Category.objects.filter(name__in=all_cat_names)}
                new_cat_names = all_cat_names - set(existing_cats.keys())
                if new_cat_names:
                    new_cats = Category.objects.bulk_create([Category(name=name) for name in new_cat_names])
                    for cat in new_cats:
                        existing_cats[cat.name] = cat

                LectureCategory = Lecture.categories.through
                lecture_category_relations = []

                for title, lecture in created_lectures_map.items():
                    for cat_name in lecture_category_map.get(title, []):
                        category = existing_cats.get(cat_name)
                        if category:
                            lecture_category_relations.append(LectureCategory(lecture_id=lecture.id, category_id=category.id))

                    for review_data in api_data_map[title].get("lecture_reviews", []):
                        reviews_to_create.append(
                            LectureReview(lecture=lecture, rating=review_data["rating"], content=review_data["content"])
                        )

                if lecture_category_relations:
                    LectureCategory.objects.bulk_create(lecture_category_relations, ignore_conflicts=True)
                if reviews_to_create:
                    LectureReview.objects.bulk_create(reviews_to_create, ignore_conflicts=True)
