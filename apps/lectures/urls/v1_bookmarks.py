from django.urls import path

from apps.lectures.views.bookmark_views import BookmarkToggleView

urlpatterns = [
    path("bookmarks/toggle", BookmarkToggleView.as_view()),
]
