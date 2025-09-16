from django.urls import path

from apps.lectures.views.bookmark_views import BookmarkView

urlpatterns = [
    path("<uuid:lecture_uuid>/bookmark", BookmarkView.as_view()),
]
