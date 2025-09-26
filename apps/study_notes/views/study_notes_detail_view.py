from uuid import UUID

from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_notes.models.study_notes import StudyNote
from apps.study_notes.Permissions import IsStudyNoteAuthor
from apps.study_notes.serializers.study_notes_serializers import (
    StudyNoteSerializer,
    StudyNoteUpdateSerializer,
)
from apps.study_notes.services.study_notes_services import StudyNoteService


class StudyNoteDetailView(APIView):
    """
    스터디 노트 조회/수정 통합 뷰
    """

    service_class = StudyNoteService

    def get_service(self) -> StudyNoteService:
        return self.service_class(s3_uploader=getattr(self, "s3_uploader", None))

    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsStudyNoteAuthor()]
        return [IsAuthenticated()]

    def get_object(self, group_uuid: UUID, note_id: int) -> StudyNote:
        return get_object_or_404(
            StudyNote.objects.select_related("author").prefetch_related("images", "attachments"),
            id=note_id,
            study_group__uuid=group_uuid,
        )

    @extend_schema(
        tags=["스터디 기록 (StudyNotes)"],
        summary="스터디 노트 상세 조회",
        description="스터디 그룹에 속한 유저가 특정 스터디 노트를 조회합니다.",
        responses={
            200: StudyNoteSerializer,
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="권한 없음",
                examples=[
                    OpenApiExample("권한 없음 예시", value={"detail": "스터디 그룹에 속한 사용자만 조회 가능합니다."})
                ],
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="노트 없음",
                examples=[OpenApiExample("노트 없음 예시", value={"detail": "해당 노트를 찾을 수 없습니다."})],
            ),
        },
    )
    def get(self, request: Request, group_uuid: UUID, note_id: int) -> Response:
        note = get_object_or_404(
            StudyNote.objects.select_related("author").prefetch_related("images", "attachments"),
            id=note_id,
            study_group__uuid=group_uuid,
            study_group__members=request.user,
        )
        serializer = StudyNoteSerializer(note)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["스터디 기록 (StudyNotes)"],
        summary="스터디 노트 수정",
        description="스터디 기록 작성자만 제목, 내용, 이미지, 첨부파일을 수정할 수 있습니다.",
        request=StudyNoteUpdateSerializer,
        responses={
            200: StudyNoteSerializer,
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="권한 없음",
                examples=[OpenApiExample("권한 없음 예시", value={"detail": "작성자만 수정할 수 있습니다."})],
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="노트 없음",
                examples=[OpenApiExample("노트 없음 예시", value={"detail": "해당 노트를 찾을 수 없습니다."})],
            ),
        },
    )
    def patch(self, request: Request, group_uuid: UUID, note_id: int) -> Response:
        """
        스터디 노트 수정
        - 작성자만 수정 가능
        - validated_data를 서비스로 그대로 전달
        """
        note = self.get_object(group_uuid, note_id)
        self.check_object_permissions(request, note)

        serializer = StudyNoteUpdateSerializer(note, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_note = self.get_service().update_study_note(note=note, **serializer.validated_data)

        return Response(StudyNoteSerializer(updated_note).data, status=status.HTTP_200_OK)
