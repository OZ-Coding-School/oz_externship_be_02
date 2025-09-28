from django.urls import path

from apps.study_notes.views.study_note_view import StudyNoteView
from apps.study_notes.views.study_notes_detail_view import StudyNoteDetailView
from apps.study_notes.views.study_notes_upload_view import StudyNoteUploadView

urlpatterns = [
    # GET, POST /api/v1/study-notes/<group_uuid>/notes - 스터디 기록 조회, 생성
    path("/<uuid:group_uuid>/notes", StudyNoteView.as_view(), name="study-notes"),
    # GET, PATCH, DELETE /api/v1/study-notes/<group_uuid>/notes/<note_id> - 스터디 노트 상세 조회, 수정, 삭제
    path("/<uuid:group_uuid>/notes/<int:note_id>", StudyNoteDetailView.as_view(), name="study-note-detail"),
    # POST /api/v1/study-notes/upload - 이미지/첨부파일 업로드
    path("study-notes/upload", StudyNoteUploadView.as_view(), name="upload-study-note-files"),
]
