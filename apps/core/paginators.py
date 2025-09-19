from typing import Any

from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response


class StandardPageNumberPagination(PageNumberPagination):
    # 한 페이지에 기본적으로 표시할 항목의 개수를 5개로 설정.
    # 클라이언트가 별도로 페이지 크기를 지정하지 않으면 이 값이 사용된다.
    page_size = 5

    # 클라이언트가 URL 쿼리 파라미터를 통해 페이지 당 항목 수를 직접 지정할 수 있도록 허용합니다.
    # 예를 들어, /api/v1/some-url/?page_size=10 와 같이 요청하면, DRF가 이 파라미터를 인식하여 페이지 크기를 10으로 동적으로 변경합니다.
    page_size_query_param = "page_size"

    # 클라이언트가 'page_size_query_param'을 통해 요청할 수 있는 최대 항목 수를 100개로 제한. 비정상적으로 많은 수의 데이터를 한 번에 요청하여 서버에 과부하를 주는 것을 방지하는 안전장치 역할
    max_page_size = 100


class DefaultCursorPagination(CursorPagination):
    """
    기본 커서 페이지네이션 클래스
    - 생성일시(created_at)의 내림차순(최신순)으로 정렬한다.
    """

    page_size = 10
    page_size_query_param = "limit"
    ordering = ("-created_at", "-id")

    def get_paginated_response(self, data: list[dict[str, Any]]) -> Response:
        return Response({"next_cursor": self.get_next_link(), "results": data})
