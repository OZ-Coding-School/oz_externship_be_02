from django.urls import path

from apps.users.views.auth_view import (
    CookieTokenRefreshAPIView,
    EmailLoginAPIView,
    LogoutAPIView,
    UserSignupAPIView,
)
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
    FindEmailSendCodeAPIView,
    FindEmailVerifyCodeAPIView,
)
from apps.users.views.social_login_views import (
    KakaoLoginCallbackView,
    NaverLoginCallbackView,
)
from apps.users.views.withdrawals_view import AccountRecoveryAPIView, WithdrawalAPIView

urlpatterns = [
    # 이메일 인증 관련
    path("auth/email/send-code", SignUpEmailVerificationSendAPIView.as_view(), name="email_send_code"),
    path("auth/email/verify", SignUpEmailVerifiCationVerifyAPIView.as_view(), name="email_verify_code"),
    path("auth/reset-password/send", PasswordResetEmailVerificationSendAPIView.as_view(), name="password_reset_send"),
    path(
        "auth/reset-password/verify",
        PassowrdResetEmailVerificationVerifyAPIView.as_view(),
        name="password_reset_verify",
    ),
    path(
        "auth/recover-account/send", AccountRecoveryEmailVerificationSendAPIView.as_view(), name="recover_account_send"
    ),
    path(
        "auth/recover-account/verify",
        AccountRecoveryEmailVerificationVerifyAPIView.as_view(),
        name="recover_account_verify",
    ),
    # 휴대폰 인증 관련
    path("auth/recover", AccountRecoveryAPIView.as_view(), name="account_recovery"),
    path("auth/phone/send-code", SendVerificationCodeAPIView.as_view(), name="phone_send_code"),
    path("auth/phone/verify", VerifyCodeAPIView.as_view(), name="phone_verify_code"),
    path("auth/find-email/send-code", FindEmailSendCodeAPIView.as_view(), name="find_email_send_code"),
    path("auth/find-email/verify", FindEmailVerifyCodeAPIView.as_view(), name="find_email_verify_code"),
    # 회원 탈퇴 관련
    path("auth/withdraw", WithdrawalAPIView.as_view(), name="account_withdrawals"),
    # 회원 가입 및 로그인 관련
    path("auth/email/signup", UserSignupAPIView.as_view(), name="signup"),
    path("auth/email/login", EmailLoginAPIView.as_view(), name="email_login"),
    # 소셜 로그인
    path("auth/kakao/callback", KakaoLoginCallbackView.as_view(), name="kakao_callback"),
    path("auth/naver/callback", NaverLoginCallbackView.as_view(), name="naver_callback"),
    # 로그아웃
    path("auth/logout", LogoutAPIView.as_view(), name="logout"),
    # 토큰 재발급
    path("auth/refresh", CookieTokenRefreshAPIView.as_view(), name="token_refresh"),
]
