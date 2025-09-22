from django.urls import path

from ..views.applications_views import ApplicationAPIView

urlpatterns = [
    # GET, POST /api/v1/recruitments/{recruitment_uuid}/applications
    path("", ApplicationAPIView.as_view(), name="recruitment-applications"),
]
