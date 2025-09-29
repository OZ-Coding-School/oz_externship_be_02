from django.urls import path

from apps.lectures.views.admin_lecture_views import (
    AdminLectureDetailView,
    AdminLectureListView,
)

urlpatterns = [
    path("", AdminLectureListView.as_view(), name="admin-lecture-list"),
    path("<int:lecture_id>", AdminLectureDetailView.as_view(), name="admin-lecture-detail"),
]
