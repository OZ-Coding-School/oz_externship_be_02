from django.urls import path

from apps.studies.views.review_views import ReviewCreateListAPIView

urlpatterns = [
    path("/<uuid:group_uuid>/reviews", ReviewCreateListAPIView.as_view(), name="review-create-list"),
    # path("/<uuid:group_uuid>/reviews", name="study-group-review-list"),
]
