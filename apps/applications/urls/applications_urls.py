from django.urls import path

from apps.applications.views.application_detail_views import (
    ApplicationApproveView,
    ApplicationDetailView,
    ApplicationRejectView,
)

# 목록 뷰 import
from ..views.my_applications_views import MyApplicationsListView

urlpatterns = [
    # '내 지원 목록' 경로
    path("/me", MyApplicationsListView.as_view(), name="my-application-list"),
    # '개별 지원 상세' 경로
    path("/<int:application_id>", ApplicationDetailView.as_view(), name="application-detail"),
    path("/<int:application_id>/approve", ApplicationApproveView.as_view(), name="application-approve"),
    path("/<int:application_id>/reject", ApplicationRejectView.as_view(), name="application-reject"),
]
