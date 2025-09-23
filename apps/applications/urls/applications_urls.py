from django.urls import path

from apps.applications.views.application_detail_views import ApplicationDetailView

urlpatterns = [
    path("applications/<int:application_id>/", ApplicationDetailView.as_view(), name="application-detail"),
]
