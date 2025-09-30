from django.urls import path

from apps.applications.views.admin_applications_views import (
    AdminApplicationsAPIView,
    AdminApplicationsDetailAPIView,
)

urlpatterns = [
    path("", AdminApplicationsAPIView.as_view(), name="admin-application-list"),
    path("/<int:application_id>", AdminApplicationsDetailAPIView.as_view(), name="admin-application-detail"),
]
