"""
프로젝트 전반에서 사용되는 페이지네이션 클래스를 정의힌디.
"""

from rest_framework.pagination import PageNumberPagination


# REQ-RECM-002/008 (태그 검색)에서 사용할 ㅍ페이지네이션
# 페이지 당 5개의 항목을 반환하는 PageNumberPagination
class FivePageNumberPagination(PageNumberPagination):
    page_size = 5
    # 요청 예시 : /api/v1/tags/?page=2 -> page=2 : 두 번째 페이지 요청
    # page는 PageNumberPagination 클래스에서 내부적으로 처리해준다.
