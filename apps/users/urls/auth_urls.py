from django.urls import path

from apps.users.views.auth_view import (
    EmailVerificationSendAPIView,
    EmailVerifyCodeAPIView,
)
from apps.users.views.withdrawals import WithdrawalAPIView

urlpatterns = [
    path("email/send-code", EmailVerificationSendAPIView.as_view(), name="send_code_email"),
    path("email/verify", EmailVerifyCodeAPIView.as_view(), name="email_verify_code"),
    path("withdraw", WithdrawalAPIView.as_view(), name="account_withdrawals"),
]
