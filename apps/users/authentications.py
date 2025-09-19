from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get("access")

        if not access_token:
            raise AuthenticationFailed("로그인이 필요합니다.")

        request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        try:
            return super().authenticate(request)
        except InvalidToken as e:
            # 예외 메시지를 확인하여 만료 여부를 정확히 판단
            if 'expired' in str(e).lower():
                raise AuthenticationFailed("토큰이 만료되었습니다.")
            else:
                raise AuthenticationFailed("유효하지 않은 토큰입니다.")
        except TokenError:
            raise AuthenticationFailed("토큰 처리 중 오류가 발생했습니다.")



"""
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework import status

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # 1. 요청 본문이 아닌 쿠키에서 refresh token을 직접 가져옵니다.
        refresh_token = request.COOKIES.get('refresh')
        
        if not refresh_token:
            return Response({"error": "리프레시 토큰이 쿠키에 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. 가져온 토큰을 request.data에 넣어 부모 클래스가 처리할 수 있도록 합니다.
        request.data['refresh'] = refresh_token
        
        # 3. 부모 클래스의 로직을 실행하여 새로운 액세스 토큰을 발급받습니다.
        response = super().post(request, *args, **kwargs)
        
        # 4. 성공적으로 재발급 받았다면, 새로운 액세스 토큰을 다시 쿠키에 설정합니다.
        if response.status_code == 200:
            access_token = response.data.get('access')
            if access_token:
                response.set_cookie('access', access_token, httponly=True, samesite='Lax')
        
        return response
"""