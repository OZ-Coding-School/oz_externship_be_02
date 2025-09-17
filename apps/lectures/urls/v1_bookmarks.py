from django.urls import path

from apps.lectures.views.bookmark_views import BookmarkListView, BookmarkView

urlpatterns = [
    path("bookmarks", BookmarkListView.as_view()),
    path("<uuid:lecture_uuid>/bookmark", BookmarkView.as_view()),
]
