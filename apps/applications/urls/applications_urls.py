from django.urls import path

from apps.applications.views.application_detail_views import (
    ApplicationApproveView,
    ApplicationDetailView,
    ApplicationRejectView,
)

urlpatterns = [
    path("/<int:application_id>", ApplicationDetailView.as_view(), name="application-detail"),
    path("/<int:application_id>/approve", ApplicationApproveView.as_view(), name="application-approve"),
    path("/<int:application_id>/reject", ApplicationRejectView.as_view(), name="application-reject"),
]
