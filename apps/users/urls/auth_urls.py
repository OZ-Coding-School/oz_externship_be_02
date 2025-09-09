from django.urls import path

from apps.users.views.email_view import (
    EmailVerificationSendAPIView,
    EmailVerifyCodeAPIView,
)
from apps.users.views.phone_view import SendVerificationCodeAPIView, VerifyCodeAPIView

urlpatterns = [
    path("email/send-code", EmailVerificationSendAPIView.as_view(), name="email_send_code"),
    path("email/verify", EmailVerifyCodeAPIView.as_view(), name="email_verify_code"),
    path("phone/send-code", SendVerificationCodeAPIView.as_view(), name="phone_send_code"),
    path("phone/verify-code", VerifyCodeAPIView.as_view(), name="phone_verify_code"),
]
