from django.urls import path

from apps.lectures.views.bookmark_views import BookmarkView

urlpatterns = [
    path("/<str:lecture_uuid>/bookmarks", BookmarkView.as_view()),
]
