import asyncio
import time
from typing import Any, Dict, List, Union, cast
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
    3. Django ORM의 bulk_create를 사용하여 데이터베이스에 대량으로 데이터를 삽입하여 N+1 쿼리 문제를 해결합니다.
    """

    help = "인프런 API에서 직접 데이터를 가져와 DB와 효율적으로 동기화합니다."

    # --- 크롤링 설정 ---
    BASE_URL = "https://course-api.inflearn.com/client/api/v1/course/search"
    REVIEW_API_URL = "https://ucc-api.inflearn.com/client/api/v1/reviews/course/{course_id}"
    PAGE_SIZE = 100  # 한 번에 요청할 강의 수
    MAX_CONCURRENT_REQUESTS = 10  # API 서버 부하를 줄이기 위한 동시 요청 수 제한

    def handle(self, *args: Any, **options: Any) -> None:
        """명령어의 메인 진입점입니다."""

        # 비동기 함수들을 실행하기 위한 메인 async 함수
        async def main() -> None:
            logger.info("인프런 API 크롤링 및 DB 동기화를 시작합니다...")
            start_time = time.time()

            # 1. API를 통해 모든 강의와 리뷰 데이터를 비동기적으로 크롤링합니다.
            processed_courses_data = await self._get_all_processed_data_from_api()

            if not processed_courses_data:
                logger.warning("API로부터 가져올 강의 데이터가 없습니다.")
                return

            # 2. 크롤링된 데이터를 데이터베이스와 동기화합니다.
            # Django ORM은 동기적으로 동작하므로, sync_to_async를 사용하여 비동기 이벤트 루프에서 안전하게 실행합니다.
            await sync_to_async(self.sync_data_with_db, thread_sensitive=True)(processed_courses_data)

            end_time = time.time()
            logger.info(f"총 실행 시간: {end_time - start_time:.2f}초")

        # 메인 비동기 함수를 실행합니다.
        asyncio.run(main())

    async def _get_all_processed_data_from_api(self) -> List[Dict[str, Any]]:
        """Inflearn API에서 모든 강의와 관련 리뷰를 비동기적으로 크롤링하여 가공합니다."""
        async with httpx.AsyncClient(timeout=20.0) as client:
            # 1. 첫 페이지를 요청하여 전체 페이지 수를 가져옵니다.
            params: Dict[str, Union[str, int]] = {
                "pageNumber": 1,
                "pageSize": self.PAGE_SIZE,
                "sort": "POPULAR",
                "lang": "ko",
            }
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                total_page = response.json().get("data", {}).get("totalPage", 1)
                logger.info(f"전체 페이지 수: {total_page}, 페이지 당 강의 수: {self.PAGE_SIZE}")
            except httpx.RequestError as e:
                logger.error(f"첫 페이지 요청 실패: {e}")
                return []

            # 2. 모든 페이지의 강의 목록을 병렬로 가져오기 위한 작업 목록을 생성합니다.
            course_tasks = [
                self._fetch_page(client, self.BASE_URL, {**params, "pageNumber": page_num})
                for page_num in range(1, total_page + 1)
            ]

            all_courses_raw = []
            # 동시 요청 수 제한을 지키며 모든 페이지의 데이터를 가져옵니다.
            for i in range(0, len(course_tasks), self.MAX_CONCURRENT_REQUESTS):
                batch = course_tasks[i : i + self.MAX_CONCURRENT_REQUESTS]
                results = await asyncio.gather(*batch, return_exceptions=True)
                for res in results:
                    if isinstance(res, list):
                        all_courses_raw.extend(res)
                    elif isinstance(res, Exception):
                        logger.warning(f"페이지 크롤링 중 오류 발생: {res}")

            # 3. 모든 강의의 리뷰를 병렬로 가져오기 위한 작업 목록을 생성합니다.
            course_id_map = {
                item.get("course", {}).get("id"): item for item in all_courses_raw if item.get("course", {}).get("id")
            }
            review_tasks = [self._fetch_reviews(client, course_id) for course_id in course_id_map.keys()]

            all_reviews_map = {}
            # 동시 요청 수 제한을 지키며 모든 리뷰 데이터를 가져옵니다.
            for i in range(0, len(review_tasks), self.MAX_CONCURRENT_REQUESTS):
                batch = review_tasks[i : i + self.MAX_CONCURRENT_REQUESTS]
                results = await asyncio.gather(*batch, return_exceptions=True)
                for res in results:
                    if isinstance(res, list):
                        if res:
                            review_dict = res[0]
                            if "course_id" in review_dict:
                                all_reviews_map[review_dict["course_id"]] = review_dict["reviews"]
                    elif isinstance(res, Exception):
                        logger.warning(f"리뷰 크롤링 중 오류 발생: {res}")

            # 4. 크롤링된 강의 데이터와 리뷰 데이터를 최종적인 형식으로 조합합니다.
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
                    "thumbnail_img_url": quote(
                        course_info.get("thumbnailUrl"),
                        safe=":/?&",
                    ),
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
        self, client: httpx.AsyncClient, url: str, params: Dict[str, Union[str, int]]
    ) -> List[Dict[str, Any]]:
        """특정 페이지의 강의 목록을 비동기적으로 가져옵니다."""
        try:
            # logger.info(f"{params.get('pageNumber')} 페이지 크롤링 중...") # 로그가 너무 많이 남으므로 주석 처리
            response = await client.get(url, params=params)
            response.raise_for_status()
            return cast(List[Dict[str, Any]], response.json().get("data", {}).get("items", []))
        except httpx.HTTPStatusError as e:
            logger.error(f"페이지 {params.get('pageNumber')} 로드 실패: {e.response.status_code}")
        except Exception as e:
            logger.error(f"페이지 {params.get('pageNumber')} 처리 중 예외 발생: {e}")
        return []

    async def _fetch_reviews(self, client: httpx.AsyncClient, course_id: int) -> List[Dict[str, Any]]:
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
            processed_reviews = []
            for review in response.json().get("data", {}).get("items", []):
                rating = rating_map.get(review.get("star"))
                if rating:
                    processed_reviews.append({"rating": rating, "content": review.get("body", "")})
            return [{"course_id": course_id, "reviews": processed_reviews}]
        except Exception:
            # 리뷰를 가져오지 못하더라도 전체 프로세스가 멈추지 않도록 예외를 처리합니다.
            return []

    def sync_data_with_db(self, courses_data: List[Dict[str, Any]]) -> None:
        """크롤링된 데이터를 데이터베이스와 동기화합니다."""
        # 1. API 데이터와 로컬 DB 데이터를 비교 준비
        # API에서 가져온 강의를 제목을 key로 하는 딕셔너리로 변환하여 접근을 용이하게 합니다.
        api_data_map = {item["title"]: item for item in courses_data if item.get("title")}
        api_titles = set(api_data_map.keys())

        # 로컬 DB에 저장된 인프런 강의들의 제목을 가져옵니다.
        local_titles = set(Lecture.objects.filter(platform=PlatformChoices.INFLEARN).values_list("title", flat=True))

        # 2. 추가할 강의와 삭제할 강의의 제목을 결정합니다.
        titles_to_add = api_titles - local_titles
        titles_to_delete = local_titles - api_titles

        # 3. 삭제할 강의를 DB에서 제거합니다.
        if titles_to_delete:
            deleted_count, _ = Lecture.objects.filter(
                platform=PlatformChoices.INFLEARN, title__in=titles_to_delete
            ).delete()
            logger.info(f"삭제된 강의 수: {deleted_count}개")

        # 4. 추가할 강의 데이터를 준비합니다.
        lectures_to_create = []
        lecture_category_map = {}  # 강의 제목과 카테고리 이름 목록을 임시로 매핑
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

        reviews_to_create = []
        # 5. 데이터베이스 작업을 트랜잭션으로 묶어 원자성을 보장합니다.
        with transaction.atomic():
            if lectures_to_create:
                # 5-1. 신규 강의를 bulk_create로 한 번에 삽입합니다.
                # ignore_conflicts=True는 기본 키 충돌 시 에러 없이 넘어가도록 합니다.
                Lecture.objects.bulk_create(lectures_to_create, ignore_conflicts=True)
                logger.info(f"신규 강의 {len(lectures_to_create)}개 생성 시도 완료.")

                # 5-2. bulk_create는 생성된 객체의 ID를 반환하지 않으므로, DB에서 다시 조회하여 ID를 확보합니다.
                created_lectures_map = {lec.title: lec for lec in Lecture.objects.filter(title__in=titles_to_add)}
                logger.info(f"DB에서 ID가 할당된 신규 강의 {len(created_lectures_map)}개 확인.")

                # 5-3. 카테고리를 효율적으로 처리합니다.
                all_cat_names = {cat for cats in lecture_category_map.values() for cat in cats}
                existing_cats = {cat.name: cat for cat in Category.objects.filter(name__in=all_cat_names)}
                new_cat_names = all_cat_names - set(existing_cats.keys())
                if new_cat_names:
                    new_cats = Category.objects.bulk_create([Category(name=name) for name in new_cat_names])
                    for cat in new_cats:
                        existing_cats[cat.name] = cat

                # 5-4. 강의-카테고리 관계(M2M)와 리뷰(FK) 데이터를 준비합니다.
                LectureCategory = Lecture.categories.through  # M2M 중간 테이블 모델
                lecture_category_relations = []

                for title, lecture in created_lectures_map.items():
                    # 카테고리 관계 준비
                    cat_names = lecture_category_map.get(title, [])
                    for cat_name in cat_names:
                        category = existing_cats.get(cat_name)
                        if category:
                            lecture_category_relations.append(
                                LectureCategory(lecture_id=lecture.id, category_id=category.id)
                            )

                    # 리뷰 데이터 준비
                    reviews_data = api_data_map[title].get("lecture_reviews", [])
                    for review_data in reviews_data:
                        reviews_to_create.append(
                            LectureReview(lecture=lecture, rating=review_data["rating"], content=review_data["content"])
                        )

                # 5-5. 준비된 관계 및 리뷰 데이터를 bulk_create로 한 번에 삽입합니다.
                if lecture_category_relations:
                    LectureCategory.objects.bulk_create(lecture_category_relations, ignore_conflicts=True)
                if reviews_to_create:
                    LectureReview.objects.bulk_create(reviews_to_create, ignore_conflicts=True)
                    logger.info(f"신규 리뷰 {len(reviews_to_create)}개 생성 완료.")

        # 6. 최종 동기화 결과를 로그로 남깁니다.
        logger.info(
            f"동기화 완료! "
            f"신규 강의 {len(lectures_to_create)}개, "
            f"삭제된 강의 {len(titles_to_delete)}개, "
            f"신규 리뷰 {len(reviews_to_create)}개."
        )
        logger.info(f"DB에 이미 존재하여 건너뛴 강의 수: {len(api_titles & local_titles)}개")
