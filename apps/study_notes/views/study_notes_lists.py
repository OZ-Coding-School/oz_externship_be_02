from uuid import UUID
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import StudyNote
from apps.study_notes.serializers.study_notes_serializers import StudyNoteListSerializer


class StudyNoteListView(APIView):
    """
    스터디 기록 전체 조회
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, group_uuid: UUID):
        group = get_object_or_404(StudyGroup, uuid=group_uuid)

        # 권한 체크: 그룹에 속한 유저
        if request.user not in group.members.all():
            return Response({"detail": "스터디 그룹에 속한 사용자만 조회 가능합니다."}, status=403)

        notes = StudyNote.objects.filter(study_group=group).order_by("-created_at")
        serializer = StudyNoteListSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
