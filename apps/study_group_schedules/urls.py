from typing import List

from django.urls import URLPattern, path

from apps.study_group_schedules import views

urlpatterns: List[URLPattern] = [
    path("", views.StudyGroupScheduleCreateView.as_view(), name="create_schedule"),
]
