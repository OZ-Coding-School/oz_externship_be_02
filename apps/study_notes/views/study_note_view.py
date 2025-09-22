from typing import Optional
from uuid import UUID

from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import get_object_or_404
from django.utils.datastructures import MultiValueDict
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import StudyNote
from apps.study_notes.serializers.study_notes_serializers import (
    StudyNoteListSerializer,
    StudyNoteSerializer,
)
from apps.study_notes.services.study_notes_services import StudyNoteService
from apps.users.models import User


class StudyNoteView(APIView):
    """
    스터디 그룹에 속한 유저가 그룹원들의 스터디 기록을 전체 조회하거나, 새로운 스터디 기록을 생성합니다.
    """

    permission_classes = [IsAuthenticated]
    service_class = StudyNoteService

    @extend_schema(
        tags=["스터디 기록 (StudyNotes)"],
        summary="스터디 기록 목록 조회",
        description="스터디 그룹에 속한 유저가 그룹원들의 스터디 기록을 전체 조회합니다.",
        responses={
            200: StudyNoteListSerializer(many=True),
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="권한 없음",
                examples=[
                    OpenApiExample(
                        "권한 없음 예시",
                        value={"detail": "스터디 그룹에 속한 사용자만 조회 가능합니다."},
                    )
                ],
            ),
        },
    )
    def get(self, request: Request, group_uuid: UUID) -> Response:
        """스터디 그룹에 속한 유저가 그룹원들의 스터디 기록을 전체 조회"""
        group = get_object_or_404(StudyGroup, uuid=group_uuid)

        # 권한 체크: 그룹에 속한 유저
        assert isinstance(request.user, User)
        if request.user not in group.members.all():
            return Response(
                {"detail": "스터디 그룹에 속한 사용자만 조회 가능합니다."}, status=status.HTTP_403_FORBIDDEN
            )

        notes = StudyNote.objects.filter(study_group=group).order_by("-created_at")
        serializer = StudyNoteListSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_service(self) -> Optional[StudyNoteService]:
        # 테스트 시 Mock을 주입할 수 있는 곳
        return self.service_class(s3_uploader=getattr(self, "s3_uploader", None))

    @extend_schema(
        tags=["스터디 기록 (StudyNotes)"],
        summary="스터디 기록 생성",
        description="스터디 그룹에 속한 사용자가 학습 기록을 작성합니다.",
        request=StudyNoteSerializer,
        responses={
            201: StudyNoteSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="ValidationError 발생 시",
                examples=[
                    OpenApiExample(
                        "ValidationError 예시",
                        value={"detail": "잘못된 요청입니다. 필수 필드가 누락되었거나 형식이 올바르지 않습니다."},
                    )
                ],
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="NotFoundError 발생 시",
                examples=[
                    OpenApiExample("NotFoundError 예시", value={"detail": "해당 스터디 그룹을 찾을 수 없습니다."})
                ],
            ),
        },
    )
    def post(self, request: Request, group_uuid: UUID) -> Response:
        """스터디 기록 생성"""
        group = get_object_or_404(StudyGroup, uuid=group_uuid)
        # request.data가 dict이면 그냥 list로 할당, QueryDict이면 setlist 사용
        data: MultiValueDict[str, list[UploadedFile] | str] = MultiValueDict(request.data)
        # 파일 추가
        data.setlist("image_files", request.FILES.getlist("images_file"))
        data.setlist("attachment_files", request.FILES.getlist("attachments_file"))
        serializer = StudyNoteSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        service = self.get_service() or self.service_class()
        assert isinstance(request.user, User)

        study_note = service.create_study_note(
            author=request.user,
            study_group=group,
            title=serializer.validated_data["title"],
            content=serializer.validated_data["content"],
            images=serializer.validated_data.get("image_files", []),
            attachments=serializer.validated_data.get("attachment_files", []),
        )
        return Response(StudyNoteSerializer(study_note).data, status=status.HTTP_201_CREATED)
