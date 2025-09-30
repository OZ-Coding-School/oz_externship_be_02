from typing import List

from django.urls import URLPattern, path

from apps.study_group_schedules import views

app_name = "study_group_schedules"

urlpatterns: List[URLPattern] = [
    # POST /api/v1/schedules
    path("", views.StudyGroupScheduleCreateView.as_view(), name="create_schedule"),
    # GET /api/v1/schedules/<uuid:study_group_id>
    path("/<uuid:study_group_id>", views.StudyGroupScheduleListView.as_view(), name="schedule_list"),
    # GET /api/v1/schedules/<uuid:study_group_id>/<int:schedule_id>
    path(
        "/<uuid:study_group_uuid>/<int:schedule_id>",
        views.StudyGroupScheduleDetailView.as_view(),
        name="schedule_detail",
    ),
    # PATCH /api/v1/schedules/<uuid:study_group_id>/<int:schedule_id>
    path(
        "/<uuid:study_group_uuid>/<int:schedule_id>",
        views.StudyGroupScheduleUpdateView.as_view(),
        name="schedule_update",
    ),
]
