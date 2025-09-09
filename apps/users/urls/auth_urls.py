from django.urls import path

from apps.users.views.email_view import (
    SignUpEmailVerificationSendAPIView,
    SignUpEmailVerifiCationVerifyAPIView,
)
from apps.users.views.phone_view import SendVerificationCodeAPIView, VerifyCodeAPIView
from apps.users.views.withdrawals import WithdrawalAPIView

urlpatterns = [
    path("email/send-code", SignUpEmailVerificationSendAPIView.as_view(), name="email_send_code"),
    path("email/verify", SignUpEmailVerifiCationVerifyAPIView.as_view(), name="email_verify_code"),
    path("phone/send-code", SendVerificationCodeAPIView.as_view(), name="phone_send_code"),
    path("phone/verify-code", VerifyCodeAPIView.as_view(), name="phone_verify_code"),
    path("withdraw", WithdrawalAPIView.as_view(), name="account_withdrawals"),
]
