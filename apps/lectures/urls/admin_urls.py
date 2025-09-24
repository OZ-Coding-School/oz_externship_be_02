from django.urls import path

from apps.lectures.views.admin_lecture_views import AdminLectureListView

urlpatterns = [
    path("", AdminLectureListView.as_view(), name="admin-lecture-list"),
]
