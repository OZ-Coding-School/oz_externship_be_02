# lectures/urls.py
from django.urls import path

from apps.lectures.views.lecture_list import LectureListView
from apps.lectures.views.lecture_reviews import LectureReviewsView
from apps.lectures.views.recommend_lecture_list import RecommendLectureListView

app_name = "lectures"

urlpatterns = [
    path("/list", LectureListView.as_view(), name="lecture_list"),
    path("/list/recommendation", RecommendLectureListView.as_view(), name="recommend_lectures"),
    path("/list/<uuid:lecture_uuid>/reviews", LectureReviewsView.as_view(), name="lecture_reviews"),
]
