from django.urls import URLPattern, URLResolver, path

from apps.users.views.email_view import (
    SignUpEmailVerificationSendAPIView,
    SignUpEmailVerifiCationVerifyAPIView,
)
from apps.users.views.phone_view import SendVerificationCodeAPIView, VerifyCodeAPIView
from apps.users.views.withdrawals import WithdrawalAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    path("auth/email/send-code", SignUpEmailVerificationSendAPIView.as_view(), name="email_send_code"),
    path("auth/email/verify", SignUpEmailVerifiCationVerifyAPIView.as_view(), name="email_verify_code"),
    path("auth/phone/send-code", SendVerificationCodeAPIView.as_view(), name="phone_send_code"),
    path("auth/phone/verify-code", VerifyCodeAPIView.as_view(), name="phone_verify_code"),
    path("auth/withdraw", WithdrawalAPIView.as_view(), name="account_withdrawals"),
]
