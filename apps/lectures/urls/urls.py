# lectures/urls.py
from django.urls import path

from apps.lectures.views.lecture_list import LectureListView

app_name = "lectures"

urlpatterns = [
    path("list/", LectureListView.as_view(), name="lecture_list"),
]
