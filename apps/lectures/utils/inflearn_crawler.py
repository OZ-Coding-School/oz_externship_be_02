# 인프런의 강의 정보 및 리뷰를 크롤링하기 위한 스크립트
# fetch_reviews 함수는 특정 강의의 리뷰를, crawl_inflearn_courses 함수는 모든 강의 정보를 가져옴.
# 스크립트 실행 시 inflearn_courses.json 파일로 결과가 저장됨.
import json
import logging
import time
from typing import Any

import requests
from django.conf import settings

if not settings.DEBUG:
    logger = logging.getLogger("django")
else:
    logger = logging.getLogger("django.server")


def fetch_reviews(course_id: int) -> list[dict[str, Any]]:
    """
    특정 강의의 리뷰 정보를 가져와 ERD에 맞게 가공하는 함수
    - course_id: 인프런 강의 ID
    - return: 가공된 리뷰 정보 리스트
    """
    # 인프런 리뷰 API URL
    review_api_url = f"https://ucc-api.inflearn.com/client/api/v1/reviews/course/{course_id}"

    # API 요청 파라미터 설정
    params: dict[str, Any] = {
        "id": course_id,
        "pageNumber": 1,
        "pageSize": 4,  # ERD에 따라 최대 4개만 저장함
        "sort": "RECOMMEND",  # 추천순으로 정렬
        "lang": "ko",  # 한국어 리뷰만 가져옴
    }

    # 별점(숫자)을 ERD의 ENUM 값으로 변환하기 위한 맵
    rating_map = {
        5: "5_OUT_OF_5_STARS",
        4: "4_OUT_OF_5_STARS",
        3: "3_OUT_OF_5_STARS",
        2: "2_OUT_OF_5_STARS",
        1: "1_OUT_OF_5_STARS",
    }

    try:
        # API GET 요청
        response = requests.get(review_api_url, params=params)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생시킴
        reviews_data = response.json()

        processed_reviews = []
        # API 응답에서 리뷰 목록을 순회하며 데이터 가공
        for review in reviews_data.get("data", {}).get("items", []):
            star = review.get("star")
            processed_review = {
                "rating": rating_map.get(star, None),  # 맵핑된 enum 값으로 변환
                "content": review.get("body", ""),  # 리뷰 내용
            }
            # 유효한 rating이 있는 경우에만 리스트에 추가
            if processed_review["rating"]:
                processed_reviews.append(processed_review)
        return processed_reviews

    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError):
        # JSON 파싱 오류나 키 오류 발생 시 빈 리스트 반환
        # 네트워크 오류 발생 시 빈 리스트 반환
        return []


def crawl_inflearn_courses() -> list[dict[str, Any]]:
    """
    인프런의 모든 강의 정보를 크롤링하여 지정된 형식으로 가공하는 함수
    - return: 가공된 전체 강의 정보 리스트
    """
    # 인프런 강의 검색 API URL
    base_url = "https://course-api.inflearn.com/client/api/v1/course/search"
    page_size = 100  # 한 페이지 당 가져올 강의 수
    all_processed_courses = []

    # 난이도 문자열을 ERD의 ENUM 값으로 변환하기 위한 맵
    difficulty_map = {
        "BEGINNER": "EASY",
        "INTERMEDIATE": "NORMAL",
        "ADVANCED": "HARD",
    }
    params: dict[str, Any] = {"pageNumber": 1, "pageSize": page_size, "sort": "POPULAR", "lang": "ko"}
    try:
        # 첫 페이지를 요청하여 전체 페이지 수를 얻음
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        total_page = data.get("data", {}).get("totalPage", 1)
        logger.info(f"전체 페이지 수: {total_page}, 페이지 당 강의 수: {page_size}")

        # 전체 페이지를 순회하며 강의 정보 크롤링
        for page_num in range(1, total_page + 1):
            params["pageNumber"] = page_num
            logger.info(f"{page_num} / {total_page} 페이지를 크롤링 중...")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            page_data = response.json()

            courses = page_data.get("data", {}).get("items", [])

            # 각 강의 정보를 순회하며 데이터 가공
            for item in courses:
                course_info = item.get("course", {})
                instructor_info = item.get("instructor", {})
                price_info = item.get("listPrice", {})
                metadata = course_info.get("metadata", {})
                course_id = item.get("id")

                # 강의 시간(초)을 분으로 변환
                duration_minutes = course_info.get("runtimeSecond", 0) // 60
                # 카테고리 정보 추출
                categories = [cat.get("title") for cat in metadata.get("categories", []) if cat.get("title")]

                api_difficulty = metadata.get("level")

                # ERD에 맞는 형식으로 데이터 가공
                processed_course = {
                    "title": course_info.get("title"),
                    "instructor": instructor_info.get("name"),
                    "average_rating": course_info.get("star", 0.0),
                    "duration": duration_minutes,
                    "difficulty": difficulty_map.get(api_difficulty, "EASY"),  # 맵핑된 enum 값, 없으면 EASY
                    "description": course_info.get("description", "").replace("\n", " "),
                    "platform": "Inflearn",
                    "original_price": price_info.get("regularPrice", 0),
                    "discount_price": price_info.get("payPrice", 0),
                    "url_link": f"https://www.inflearn.com/course/{course_info.get('slug')}",
                    "thumbnail_img_url": course_info.get("thumbnailUrl"),
                    "categories": categories,
                    "lecture_reviews": fetch_reviews(course_id),  # 각 강의의 리뷰 정보 가져오기
                }
                all_processed_courses.append(processed_course)

            # API 서버 부하를 줄이기 위해 1초 대기
            time.sleep(1)

        return all_processed_courses

    except requests.exceptions.RequestException as e:
        logger.error(f"API 요청 중 오류가 발생했습니다: {e}")
        return []
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"API 응답을 파싱하는 데 실패했습니다: {e}")
        return []


# 이 스크립트가 직접 실행될 때만 아래 코드 블록을 실행함
if __name__ == "__main__":
    crawled_data = crawl_inflearn_courses()
    if crawled_data:
        logger.info(f"총 {len(crawled_data)}개의 강의 정보를 가져왔습니다.")
        # 크롤링된 데이터를 JSON 파일로 저장
        with open("inflearn_courses.json", "w", encoding="utf-8") as f:
            json.dump(crawled_data, f, indent=4, ensure_ascii=False)
        logger.info("결과가 inflearn_courses.json 파일로 저장되었습니다.")
