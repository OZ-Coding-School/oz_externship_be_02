from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import StudyNote
from apps.study_notes.serializers.study_notes_serializers import StudyNoteSerializer
from apps.users.models import User


class StudyNoteDetailView(APIView):
    """
    스터디 노트 상세 조회
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, group_uuid: UUID, note_id: int) -> Response:
        group = get_object_or_404(StudyGroup, uuid=group_uuid)
        note = get_object_or_404(StudyNote, id=note_id, study_group=group)

        # 권한 체크: 그룹에 속한 유저
        assert isinstance(request.user, User)
        if request.user not in group.members.all():
            return Response(
                {"detail": "스터디 그룹에 속한 사용자만 조회 가능합니다."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = StudyNoteSerializer(note)
        return Response(serializer.data, status=status.HTTP_200_OK)
