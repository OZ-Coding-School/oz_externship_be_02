from typing import Any, cast

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_group_schedules.enums import ScheduleOrdering
from apps.study_group_schedules.models import GroupSchedule
from apps.study_group_schedules.serializers.schedule_serializers import (
    StudyGroupScheduleCreateSerializer,
    StudyGroupScheduleDetailSerializer,
    StudyGroupScheduleListQueryParamsSerializer,
    StudyGroupScheduleResponseSerializer,
)
from apps.study_group_schedules.services.schedule_services import (
    get_user_accessible_schedules,
)
from apps.users.models import User


@extend_schema(
    request=StudyGroupScheduleCreateSerializer,
    responses={201: StudyGroupScheduleResponseSerializer},
    summary="스터디 그룹 스케줄 생성",
    description="새로운 스터디 그룹 스케줄을 생성합니다.",
    tags=["Study Group Schedules"],
)
class StudyGroupScheduleCreateView(APIView):
    """스터디 그룹 스케줄 생성"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = StudyGroupScheduleCreateSerializer(data=request.data)

        if serializer.is_valid():
            schedule = serializer.save()
            response_serializer = StudyGroupScheduleResponseSerializer(schedule)

            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudyGroupSchedulePagination(PageNumberPagination):
    """스터디 그룹 스케줄 페이지네이션"""

    page_size = 10
    page_size_query_param = "size"
    max_page_size = 100


@extend_schema(
    responses={200: StudyGroupScheduleResponseSerializer(many=True)},
    summary="스터디 그룹 스케줄 목록 조회",
    description="특정 스터디 그룹의 모든 스케줄을 조회합니다.",
    tags=["Study Group Schedules"],
)
class StudyGroupScheduleListView(ListAPIView[GroupSchedule]):
    """스터디 그룹 스케줄 목록 조회"""

    serializer_class = StudyGroupScheduleResponseSerializer
    pagination_class = StudyGroupSchedulePagination
    permission_classes = [IsAuthenticated]
    validated_query_params: dict[str, Any]

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # 쿼리 파라미터 검증
        qp = StudyGroupScheduleListQueryParamsSerializer(data=self.request.query_params)
        qp.is_valid(raise_exception=True)
        self.validated_query_params = qp.validated_data

        return super().list(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[GroupSchedule]:
        """스터디 그룹 스케줄 쿼리셋 반환 (services 사용)"""
        user = cast(User, self.request.user)
        study_group_uuid = self.kwargs.get("study_group_id")  # URL에서 가져옴
        start_date = self.validated_query_params.get("start_date")
        end_date = self.validated_query_params.get("end_date")
        ordering = self.validated_query_params.get("ordering", ScheduleOrdering.default())

        # 서비스를 통해 사용자가 접근 가능한 스케줄 조회
        try:
            queryset = get_user_accessible_schedules(
                user_id=user.id,
                study_group_uuid=study_group_uuid,
                start_date=start_date,
                end_date=end_date,
                ordering=ordering,
            )
            return queryset
        except ValueError:
            # UUID 형식 오류인 경우 빈 쿼리셋 반환
            return GroupSchedule.objects.none()


@extend_schema(
    responses={
        200: StudyGroupScheduleDetailSerializer,
        401: {"description": "인증되지 않은 사용자입니다."},
        403: {"description": "해당 스케줄에 대한 접근 권한이 없습니다."},
        404: {"description": "해당 스케줄을 찾을 수 없습니다."},
    },
    summary="스터디 그룹 스케줄 상세 조회",
    description="""
    특정 스터디 그룹의 개별 스케줄 상세 정보를 조회합니다. 

    스케줄 상세 조회 항목
    -  스케줄 명
    -  스터디 목표
    -  스터디 약속일 ( 캘린더 내 약속일에 해당 스케줄을 배치 )
    -  스터디 약속 시작 시간 및 종료시간 ( HH시 MM분 ~ HH시 MM분 )
    -  참여자 목록
        -  참여자 닉네임
        -  리더 여부
    """,
    tags=["Study Group Schedules"],
)
class StudyGroupScheduleDetailView(APIView):
    """스터디 그룹 스케줄 상세 조회"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, study_group_id: str, schedule_id: int) -> Response:
        """개별 스케줄 상세 정보 조회"""
        user = cast(User, request.user)

        try:
            schedule_exists = GroupSchedule.schedules.filter(id=schedule_id, study_group__uuid=study_group_id).exists()

            if not schedule_exists:
                return Response({"detail": "해당 스케줄을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

            schedule = (
                GroupSchedule.schedules.filter_accessible_by_user_and_group(
                    user_id=user.id, study_group_uuid=study_group_id
                )
                .filter(id=schedule_id)
                .get_with_detailed_info()
                .first()
            )

            if not schedule:
                return Response(
                    {"detail": "해당 스케줄에 대한 접근 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
                )

            serializer = StudyGroupScheduleDetailSerializer(schedule)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError:
            return Response({"detail": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
