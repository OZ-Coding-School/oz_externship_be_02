# apps/study_notes/study_notes_url.py
from django.urls import path

from apps.study_notes.views.study_notes_views import StudyNoteCreateView

app_name = "study_notes"

urlpatterns = [
    # Post /api/v1/study/<group_uuid>/notes/ - 스터디 기록 생성
    path("/<uuid:group_uuid>/notes", StudyNoteCreateView.as_view(), name="create-study-note"),
]
