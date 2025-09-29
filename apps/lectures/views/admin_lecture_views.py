from __future__ import annotations

from django.db.models import Q, QuerySet
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.permissions import AdminOnly
from apps.lectures.serializers.admin_lecture_serializers import (
    AdminLectureDetailSerializer,
    AdminLectureListSerializer,
)


class AdminLectureLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class AdminLectureListView(ListAPIView[Lecture]):
    permission_classes = [permissions.IsAuthenticated, AdminOnly]
    serializer_class = AdminLectureListSerializer
    pagination_class = AdminLectureLimitOffsetPagination

    @extend_schema(
        tags=["관리자"],
        summary="강의 관리 목록 조회",
        description="관리자 권한으로 강의의 목록을 조회한다.",
        parameters=[
            OpenApiParameter(name="limit", type=int, location="query", required=False, description="데이터 수"),
            OpenApiParameter(name="offset", type=int, location="query", required=False, description="시작 위치"),
            OpenApiParameter(name="search", type=str, location="query", required=False, description="강의/강사명 검색"),
        ],
        responses={200: AdminLectureListSerializer(many=True)},
    )
    def get_queryset(self) -> QuerySet[Lecture]:
        qs: QuerySet[Lecture] = Lecture.objects.all().order_by("-created_at", "-pk")
        keyword = self.request.query_params.get("search")
        if keyword:
            qs = qs.filter(Q(title__icontains=keyword) | Q(instructor__icontains=keyword))
        return qs


@extend_schema_view(
    retrieve=extend_schema(
        tags=["관리자"],
        summary="강의 관리 상세 조회",
        description="관리자 권한으로 특정 강의의 상세 정보를 조회한다.",
        responses={200: AdminLectureDetailSerializer},
    )
)
class AdminLectureDetailView(RetrieveAPIView[Lecture]):
    permission_classes = [permissions.IsAuthenticated, AdminOnly]
    serializer_class = AdminLectureDetailSerializer
    queryset = Lecture.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "lecture_id"
