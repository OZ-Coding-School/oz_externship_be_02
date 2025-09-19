from django.urls import path

from apps.users.views.auth_view import UserSignupAPIView
from apps.users.views.email_verification_view import (
    AccountRecoveryEmailVerificationSendAPIView,
    AccountRecoveryEmailVerificationVerifyAPIView,
    PassowrdResetEmailVerificationVerifyAPIView,
    PasswordResetEmailVerificationSendAPIView,
    SignUpEmailVerificationSendAPIView,
    SignUpEmailVerifiCationVerifyAPIView,
)
from apps.users.views.phone_verification_view import (
    SendVerificationCodeAPIView,
    VerifyCodeAPIView,
)
from apps.users.views.withdrawals_view import AccountRecoveryAPIView, WithdrawalAPIView

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
    path("auth/phone/verify", VerifyCodeAPIView.as_view(), name="phone_verify_code"),
    path("auth/withdraw", WithdrawalAPIView.as_view(), name="account_withdrawals"),
    path("auth/email/signup", UserSignupAPIView.as_view(), name="signup"),
    path("auth/recover", AccountRecoveryAPIView.as_view(), name="account_recovery"),
]
