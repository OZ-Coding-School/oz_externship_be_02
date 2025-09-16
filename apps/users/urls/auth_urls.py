from django.urls import path

from apps.users.views.email_view import (
    AccountRecoveryEmailVerificationSendAPIView,
    AccountRecoveryEmailVerificationVerifyAPIView,
    PassowrdResetEmailVerificationVerifyAPIView,
    PasswordResetEmailVerificationSendAPIView,
    SignUpEmailVerificationSendAPIView,
    SignUpEmailVerifiCationVerifyAPIView,
)
from apps.users.views.phone_view import SendVerificationCodeAPIView, VerifyCodeAPIView
from apps.users.views.social_user import KakaoLoginCallbackView
from apps.users.views.withdrawals import WithdrawalAPIView

urlpatterns = [
    path("auth/email/send-code", SignUpEmailVerificationSendAPIView.as_view(), name="email_send_code"),
    path("auth/email/verify", SignUpEmailVerifiCationVerifyAPIView.as_view(), name="email_verify_code"),
    path("auth/reset-password/send", PasswordResetEmailVerificationSendAPIView.as_view(), name="password_reset_send"),
    path(
        "auth/reset-password/verify",
        PassowrdResetEmailVerificationVerifyAPIView.as_view(),
        name="password_reset_verify",
    ),
    path(
        "auth/recover-account/sned", AccountRecoveryEmailVerificationSendAPIView.as_view(), name="recover_account_send"
    ),
    path(
        "auth/recover-account/verify",
        AccountRecoveryEmailVerificationVerifyAPIView.as_view(),
        name="recover_account_verify",
    ),
    path("auth/phone/send-code", SendVerificationCodeAPIView.as_view(), name="phone_send_code"),
    path("auth/phone/verify-code", VerifyCodeAPIView.as_view(), name="phone_verify_code"),
    path("auth/withdraw", WithdrawalAPIView.as_view(), name="account_withdrawals"),
    path("auth/kakao/callback", KakaoLoginCallbackView.as_view(), name="kakao_callback"),
]
