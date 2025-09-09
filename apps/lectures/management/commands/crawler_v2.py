import time
from typing import Any, Dict, List, Union
from urllib.parse import quote

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.logger import logger
from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import (
    Lecture,
    PlatformChoices,
)
from apps.lectures.serializers import LectureReviewSerializer, LectureSerializer


class Command(BaseCommand):
    help = "인프런 API에서 직접 데이터를 가져와 DB와 효율적으로 동기화합니다 (파일 저장 없음)."

    BASE_URL = "https://course-api.inflearn.com/client/api/v1/course/search"
    REVIEW_API_URL = "https://ucc-api.inflearn.com/client/api/v1/reviews/course/{course_id}"
    PAGE_SIZE = 100

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("인프런 API 크롤링 및 DB 동기화를 시작합니다...")

        # 1. API를 통해 모든 강의 데이터를 크롤링하고 가공 (메모리에서만 처리)
        processed_courses_data = self._get_all_processed_data_from_api()

        if not processed_courses_data:
            logger.warning("API로부터 가져올 강의 데이터가 없습니다.")
            return

        # 2. 가공된 데이터를 DB와 동기화
        self.sync_data_with_db(processed_courses_data)

    def _get_all_processed_data_from_api(self) -> List[Dict[str, Any]]:
        """
        인프런의 모든 강의 정보를 크롤링하여 지정된 형식으로 가공하는 메소드.
        (기존 inflearn_crawler.py의 crawl_inflearn_courses 함수 로직)
        """
        try:
            params: Dict[str, Union[str, int]] = {
                "pageNumber": 1,
                "pageSize": self.PAGE_SIZE,
                "sort": "POPULAR",
                "lang": "ko",
            }
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            total_page = response.json().get("data", {}).get("totalPage", 1)
            logger.info(f"전체 페이지 수: {total_page}, 페이지 당 강의 수: {self.PAGE_SIZE}")

            all_processed_courses = []
            for page_num in range(1, total_page + 1):
                params["pageNumber"] = page_num
                logger.info(f"{page_num} / {total_page} 페이지를 크롤링 중...")
                response = requests.get(self.BASE_URL, params=params)
                response.raise_for_status()

                courses_on_page = response.json().get("data", {}).get("items", [])
                for item in courses_on_page:
                    course_info = item.get("course", {})
                    course_id = course_info.get("id")
                    if not course_id:
                        continue

                    # --- 데이터 가공 (JSON 형식과 동일하게) ---
                    processed_course = {
                        "title": course_info.get("title"),
                        "instructor": item.get("instructor", {}).get("name"),
                        "average_rating": course_info.get("star", 0.0),
                        "duration": course_info.get("runtimeSecond", 0) // 60,
                        "difficulty": {"초급": "easy", "중급": "normal", "고급": "hard"}.get(
                            course_info.get("metadata", {}).get("level"), "easy"
                        ),
                        "description": course_info.get("description", "").replace("\n", " "),
                        "platform": "Inflearn",
                        "original_price": item.get("listPrice", {}).get("regularPrice", 0),
                        "discount_price": item.get("listPrice", {}).get("payPrice", 0),
                        "url_link": f"https://www.inflearn.com/course/{course_info.get('slug')}",
                        "thumbnail_img_url": quote(course_info.get("thumbnailUrl"), safe=":/=?&"),
                        "categories": [
                            cat.get("title")
                            for cat in course_info.get("metadata", {}).get("categories", [])
                            if cat.get("title")
                        ],
                        "lecture_reviews": self._fetch_reviews(course_id),
                    }
                    all_processed_courses.append(processed_course)
                time.sleep(1)
            return all_processed_courses
        except Exception as e:
            logger.error(f"API 크롤링/가공 중 오류 발생: {e}", exc_info=True)
            return []

    def _fetch_reviews(self, course_id: int) -> List[Dict[str, Any]]:
        # (이전과 동일)
        params: Dict[str, Union[str, int]] = {"pageNumber": 1, "pageSize": 4, "sort": "RECOMMEND", "lang": "ko"}
        rating_map = {
            5: "5_OUT_OF_5_STARS",
            4: "4_OUT_OF_5_STARS",
            3: "3_OUT_OF_5_STARS",
            2: "2_OUT_OF_5_STARS",
            1: "1_OUT_OF_5_STARS",
        }
        try:
            response = requests.get(self.REVIEW_API_URL.format(course_id=course_id), params=params)
            response.raise_for_status()
            processed_reviews = []
            for review in response.json().get("data", {}).get("items", []):
                rating = rating_map.get(review.get("star"))
                if rating:
                    processed_reviews.append({"rating": rating, "content": review.get("body", "")})
            return processed_reviews
        except Exception as e:
            logger.warning(f"강의 ID {course_id}의 리뷰를 가져오는 데 실패했습니다. Error : {e}", exc_info=True)
            return []

    def sync_data_with_db(self, courses_data: List[Dict[str, Any]]) -> None:
        # (이전 동기화 로직과 동일)
        api_data_map = {item.get("title"): item for item in courses_data if item.get("title")}
        api_titles = set(api_data_map.keys())
        local_titles = set(Lecture.objects.filter(platform=PlatformChoices.INFLEARN).values_list("title", flat=True))
        titles_to_add = api_titles - local_titles
        titles_to_delete = local_titles - api_titles

        if titles_to_delete:
            deleted_count, _ = Lecture.objects.filter(
                platform=PlatformChoices.INFLEARN, title__in=titles_to_delete
            ).delete()
            logger.info(f"삭제된 강의 수: {deleted_count}개")

        new_lectures_count = 0
        new_reviews_count = 0
        with transaction.atomic():
            for title in titles_to_add:
                item = api_data_map[title]
                data_to_save = {
                    "title": item.get("title"),
                    "instructor": item.get("instructor"),
                    "average_rating": item.get("average_rating", 0.0),
                    "duration": item.get("duration", 0),
                    "difficulty": item.get("difficulty", "easy"),
                    "description": item.get("description", ""),
                    "platform": PlatformChoices.INFLEARN,
                    "original_price": item.get("original_price", 0),
                    "discount_price": item.get("discount_price", 0),
                    "url_link": item.get("url_link"),
                    "thumbnail_img_url": item.get("thumbnail_img_url"),
                }
                serializer = LectureSerializer(data=data_to_save)
                if not serializer.is_valid():
                    logger.error(f"신규 강의 유효성 검사 실패: {title} - {serializer.errors}")
                    continue

                lecture_obj = serializer.save()
                new_lectures_count += 1

                category_names = item.get("categories", [])
                if category_names:
                    category_objects = [
                        Category.objects.get_or_create(name=cat_name.strip())[0] for cat_name in category_names
                    ]
                    lecture_obj.categories.set(category_objects)

                reviews_data = item.get("lecture_reviews", [])
                for review_data in reviews_data:
                    review_data["lecture"] = lecture_obj.pk
                    review_serializer = LectureReviewSerializer(data=review_data)
                    if review_serializer.is_valid():
                        review_serializer.save()
                        new_reviews_count += 1
                    else:
                        logger.error(f"신규 리뷰 유효성 검사 실패: {title} - {review_serializer.errors}")

        logger.info(
            f"동기화 완료! 신규 강의 {new_lectures_count}개, 삭제된 강의 {len(titles_to_delete)}개, 신규 리뷰 {new_reviews_count}개."
        )
        logger.info(f"DB에 이미 존재하여 건너뛴 강의 수: {len(api_titles & local_titles)}개")
