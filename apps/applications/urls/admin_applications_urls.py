from django.urls import path

from apps.applications.views.admin_applications_views import AdminApplicationsAPIView

urlpatterns = [
    path("", AdminApplicationsAPIView.as_view(), name="admin-application-list"),
]