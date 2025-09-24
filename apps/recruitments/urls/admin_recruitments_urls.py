from django.urls import path

from apps.recruitments.views.admin_recruitments_views import AdminRecruitmentListView

urlpatterns = [
    path("", AdminRecruitmentListView.as_view(), name="admin-recruitment-list"),
]
