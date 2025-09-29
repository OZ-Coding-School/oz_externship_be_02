from django.urls import path

from apps.recruitments.views.admin_recruitments_views import (
    AdminRecruitmentDetailView,
    AdminRecruitmentListView,
)

urlpatterns = [
    path("", AdminRecruitmentListView.as_view(), name="admin-recruitment-list"),
    path("/<int:recruitment_id>", AdminRecruitmentDetailView.as_view(), name="admin-recruitment-detail"),
    path("/<int:recruitment_id>/delete", AdminRecruitmentDetailView.as_view(), name="admin-recruitment-delete"),
]
