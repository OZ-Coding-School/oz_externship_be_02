from django.urls import path

from apps.studies.views.review_views import (
    ReviewCreateListUpdateAPIView,
    ReviewUpdateView,
)

urlpatterns = [
    path("/<uuid:group_uuid>/reviews", ReviewCreateListUpdateAPIView.as_view(), name="review-create-list"),
    path(
        "/<uuid:group_uuid>/reviews/<int:review_id>",
        ReviewUpdateView.as_view(),
        name="review-update",
    ),
]
