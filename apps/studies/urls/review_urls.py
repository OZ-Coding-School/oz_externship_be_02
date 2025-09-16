from django.urls import path

from apps.studies.views.review_views import (
    ReviewCreateAPIView,
    StudyGroupReviewListView,
)

urlpatterns = [
    path("/reviews", ReviewCreateAPIView.as_view(), name="review-create"),
    path("/reviews/<uuid:group_uuid>/", StudyGroupReviewListView.as_view(), name="study-group-review-list"),
]
