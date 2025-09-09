from rest_framework import filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.paginators import StandardPageNumberPagination
from apps.recruitments.models.tags import Tag
from apps.recruitments.serializers.tags_serializers import TagSerializer
from apps.recruitments.services.tags_services import TagService


class TagAPIView(APIView):
    """
    태그 모델에 대한 C(Create), R(Read) 기능을 처리하는 API 뷰.

    - GET: 태그 목록을 조회하고, 쿼리 파라미터를 통해 검색 및 페이지네이션을 지원한다.
    - POST: 새로운 태그를 생성한다.
    """

    # --- 클래스 변수 설정 ---
    # 이 View에서 사용할 Serializer, Permission, Paginator, Filter 등을 미리 정의한다.
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get(self, request: Request) -> Response:
        """
        GET 요청을 처리하여 태그 목록을 반환한다.
        """
        # 1. 모든 태그를 이름순으로 정렬하여 기본 쿼리셋을 준비한다.
        #    - 기본적으로 order_by를 사용하여 오름차순으로 정렬하도록 하였으며 이후 추가적인 작업을 통해 정렬방식을 선택할 수 있도록 기능을 추가할 예정
        queryset = Tag.objects.all().order_by("name")
        response: Response

        # 2. 클래스 변수 'filter_backends'에 정의된 필터들을 순회하며 적용한다.
        #    - SearchFilter가 'search_fields'를 참조하여, ?search=... 쿼리 파라미터가 있으면 쿼리셋을 필터링한다.
        for backend in self.filter_backends:
            queryset = backend().filter_queryset(request, queryset, self)

        # 3. 클래스 변수 'pagination_class'를 사용하여 페이지네이션 객체를 생성한다.
        paginator = self.pagination_class()
        # 쿼리셋에 페이지네이션을 시도한다. 페이지네이션이 비활성화된 경우(예: page_size=None) None을 반환할 수 있다.
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        # 4. 페이지네이션 적용 여부에 따라 분기하여 최종 응답(Response) 객체를 생성한다.
        if paginated_queryset is not None:
            # 페이지네이션이 적용된 경우: 직렬화 후, 페이지 정보(count, next, previous)를 포함한 응답을 생성한다.
            serializer = self.serializer_class(paginated_queryset, many=True)
            response = paginator.get_paginated_response(serializer.data)
        else:
            # 페이지네이션이 적용되지 않은 경우: 전체 쿼리셋을 직렬화하여 일반 응답을 생성한다.
            serializer = self.serializer_class(queryset, many=True)
            response = Response(serializer.data)

        # 5. 생성된 응답 객체를 반환한다.
        return response

    def post(self, request: Request) -> Response:
        """
        POST 요청을 처리하여 새로운 태그를 생성합니다.
        """
        # 1. 요청 데이터를 Serializer에 전달하여 유효성을 검증한다.
        #    - is_valid(raise_exception=True)는 유효성 검증 실패 시, 400 Bad Request 응답을 자동으로 발생시킨다.
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. 유효성 검증을 통과한 데이터로 비즈니스 로직(서비스 계층)을 호출한다.
        name = serializer.validated_data["name"].strip()
        if not name:
            return Response({"detail": "Tag name cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        # 서비스 계층에 태그 생성을 위임하여, View는 핵심 로직의 상세 구현을 알 필요가 없도록 한다. (관심사 분리)
        tag_service = TagService()
        tag = tag_service.create_tag(name=name)

        # 3. 성공적으로 생성된 태그 객체를 직렬화하여 201 Created 응답을 반환한다.
        response_serializer = self.serializer_class(tag)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
