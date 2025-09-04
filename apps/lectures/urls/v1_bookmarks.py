from django.urls import path

from apps.lectures.views.bookmark_views import BookmarkAddView, BookmarkCancelView

urlpatterns = [
    path("<int:lecture_id>/bookmarks/add", BookmarkAddView.as_view()),
    path("<int:lecture_id>/bookmarks/cancel", BookmarkCancelView.as_view()),
]
