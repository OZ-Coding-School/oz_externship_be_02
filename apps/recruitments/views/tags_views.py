"""
태그 API의 HTTP 요청/응답을 처리한다.
"""
from typing import Any
from django.db import IntegrityError
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.paginators import FivePageNumberPagination
from apps.recruitments.models.tags import Tag
from apps.recruitments.serializers.tags_serializers import TagSerializer
from apps.recruitments.services.tags_services import TagService


class TagViewSet(viewsets.ModelViewSet[Tag]):
    """
    태그를 검색하고 생성하는 API

    - GET: ?search={keyword} 로 태그를 검색합니다. (페이지 당 5개)
    - POST: {'name': 'new_tag'} 로 새로운 태그를 생성합니다.
    """
    # --- GET 요청 관련 설정 ---
    # GET 요청이 오면 ModelViewSet에 내장된 .list() 기능이 해당 요청을 처리하도록 결정한다.
    queryset = Tag.objects.all().order_by('name') # TagViewSet이 처리할 데이터베이스 쿼리셋을 정의한다. 모든 태그를 이름순으로 정렬한다.
    serializer_class = TagSerializer # TagViewSet이 데이터 직렬화/역직렬화에 사용할 클래스를 지정한다.
    permission_classes = [IsAuthenticated] # TagViewSet에 접근하기 위해 필요한 권한을 지정한다. 로그인된 사용자만 접근 가능.
    pagination_class = FivePageNumberPagination # TagViewSet에서 사용할 페이지네이션 클래스를 지정한다. (페이지 당 5개)
    filter_backends = [filters.SearchFilter] # TagViewSet에서 사용할 필터 백엔드를 지정한다. 여기서는 검색 기능을 사용한다.
    search_fields = ['name'] # SearchFilter가 적용될 필드를 지정한다. 'name' 필드를 기준으로 검색한다.

    # --- POST 요청(생성) 로직 수정 ---
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        새로운 태그를 생성하기 위해 Service Layer를 호출한다.
        """
        # 1. Serializer로 요청 데이터의 형식을 검증합니다.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Service를 인스턴스화하고, 비즈니스 로직을 위임한다.
        tag_service = TagService()
        name = serializer.validated_data['name'].strip()

        # 2-1. 이름이 비어있는지에 대한 간단한 검증은 View에서 처리할 수 있다.
        if not name:
            return Response({"detail": "Tag name cannot be empty."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2-2. 핵심 로직(중복 검사 및 생성)을 Service에 요청한다.
            tag = tag_service.create_tag(name=name)
        except IntegrityError as e:
            # 3. Service에서 중복 에러가 발생하면, 409 Conflict 응답을 반환한다.
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

        # 4. 성공 시, 생성된 객체 정보로 201 Created 응답을 반환한다.
        response_serializer = self.get_serializer(tag)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)