from django.urls import path

from apps.studies.views.admin_review_views import (
    AdminReviewDetailView,
    AdminReviewListView,
)

urlpatterns = [
    path("/reviews", AdminReviewListView.as_view(), name="admin-review-list"),
    path("/reviews/<int:pk>", AdminReviewDetailView.as_view(), name="admin-review-detail"),
]
