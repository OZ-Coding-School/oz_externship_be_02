from django.urls import path

from apps.studies.views.review_views import ReviewCreateAPIView

urlpatterns = [
    path("", ReviewCreateAPIView.as_view(), name="review-create"),
]
