# lectures/urls.py
from django.urls import path

from apps.lectures.views.lecture_list import LectureListView
from apps.lectures.views.lecture_reviews import LectureReviewsView

app_name = "lectures"

urlpatterns = [
    path("/list", LectureListView.as_view(), name="lecture_list"),
    path("/list/<uuid:lecture_uuid>/reviews", LectureReviewsView.as_view(), name="lecture_reviews"),
]
