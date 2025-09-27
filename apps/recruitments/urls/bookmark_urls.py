from django.urls import path

from ..views.bookmark_views import (
    BookmarkToggleView,
    MyBookmarkedRecruitmentListView,
)

urlpatterns = [
    path("me", MyBookmarkedRecruitmentListView.as_view(), name="my-bookmark-list"),
    path("", BookmarkToggleView.as_view(), name="recruitment-bookmark"),
]
