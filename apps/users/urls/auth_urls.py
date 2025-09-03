from django.urls import path

from apps.users.views import auth_view
from apps.users.views.auth_view import VerificationView

urlpatterns = [
    path("verify-email/", VerificationView.as_view(), name="verify_email"),
]
