from django.urls import path

from apps.users.views.auth_view import (
    EmailVerificationSendAPIView,
    EmailVerifyCodeAPIView,
)

urlpatterns = [
    path("auth/email/send-code", EmailVerificationSendAPIView.as_view(), name="send_code_email"),
    path("auth/email/verify", EmailVerifyCodeAPIView.as_view(), name="email_verify_code"),
]
