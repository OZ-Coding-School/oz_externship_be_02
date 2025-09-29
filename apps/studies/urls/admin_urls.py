from django.urls import path

from apps.studies.views.admin_review_views import AdminReviewListView

urlpatterns = [
    path("/reviews", AdminReviewListView.as_view(), name="admin-review-list"),
]
