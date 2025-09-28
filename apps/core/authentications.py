from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthenticationOrReadOnly(JWTAuthentication):
    """
    GET 메서드: 인증 미적용 (공개 접근 허용)
    다른 메서드: JWT 인증 적용 (토큰 미제공 시 에러 발생)
    """

    def authenticate(self, request):
        if request.method == "GET":
            return None  # GET은 인증 스킵

        auth_result = super().authenticate(request)
        if auth_result is None:
            # 토큰이 없으면 명시적 에러 발생
            raise exceptions.AuthenticationFailed("Authentication credentials were not provided.")
        return auth_result
