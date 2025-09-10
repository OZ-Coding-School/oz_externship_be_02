from typing import List

from django.urls import URLPattern, path

from apps.study_group_schedules import views

app_name = "study_group_schedules"

urlpatterns: List[URLPattern] = [
    # POST /api/v1/schedules
    path("", views.StudyGroupScheduleCreateView.as_view(), name="create_schedule"),
]
