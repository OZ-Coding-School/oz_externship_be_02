# apps/users/views/user_info_view.py

from typing import cast

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models.user import User
from apps.users.serializers.user_info_serializer import UserInfoSerializer
from apps.users.services.user_info_service import (
    UserInfoEditService,
    UserInfoService,
)


# 로그인한 사용자만 접근할 수 있는 APIView 기본 클래스: permission_classes를 IsAuthenticated로 고정
class AuthenticatedAPIview(APIView):
    permission_classes = [IsAuthenticated]


# 사용자 정보 조회 extend_schema
@extend_schema(
    summary="내 정보 조회",  # API 목적 요약
    description="로그인한 사용자가 자신의 정보를 조회합니다.",  # API 설명
    responses={
        200: OpenApiResponse(description="사용자 정보 조회 성공."),  # 성공 응답
        401: OpenApiResponse(
            description="인증 정보 없음. 로그인 필요."
        ),  # 실패 응답(인증 정보가 없음: 비로그인 사용자 등)
        403: OpenApiResponse(
            description="권한 없는 사용자."
        ),  # 실패 응답(인증은 됐지만 권한이 없음: 로그인 후 타 사용자의 정보를 조회하려는 경우 등)
    },
)

# 사용자 정보 조회
class UserInfoView(AuthenticatedAPIview):
    def get(self, request: Request) -> Response:
        """
        자신(로그인한 사용자)의 정보 조회.
        """
        user = cast(User, request.user)
        service = UserInfoService(user)  # 서비스 호출
        data = service.get_user_info()

        return Response(data, status=status.HTTP_200_OK)


# 사용자 정보 수정 extend_schema
@extend_schema(
    summary="내 정보 수정",  # API 목적 요약
    description="로그인한 사용자가 자신의 정보를 수정합니다. 휴대폰 번호 변경 시 인증 코드 검증이 필요합니다.",  # API 설명
    request={  # 어떤 필드를 수정할 수 있는지 시각화
        "application/json": {
            "type": "object",
            "properties": {
                "profile_img_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "프로필 이미지의 URL",
                },  # profile_img_url = models.URLField(max_length=255, null=True, blank=True, help_text="프로필 이미지")
                "password": {"type": "string", "example": "newpassword"},
                "nickname": {"type": "string", "example": "newnickname"},
                "phone_number": {"type": "string", "example": "01012345678"},
                "verification_code": {"type": "string", "example": "123456"},  # 수정은 불가
            },
            "required": ["phone_number"],
        }
    },
    responses={  # 어떤 상황에서 발생하는지에 관한 설명
        200: OpenApiResponse(description="회원 정보 수정 성공."),  # 성공 응답(모든 필드 유효)
        400: OpenApiResponse(
            description="요청 데이터 오류 또는 인증 코드 검증 실패."
        ),  # 실패 응답(요청 자체가 잘못됨: 정보 편집 시 필수 데이터를 빠트리고 저장한 경우 등)
        401: OpenApiResponse(
            description="인증 코드 없음 혹은 인증 실패."
        ),  # 실패 응답(인증되지 않았거나 인증 정보가 없음: 로그인이 필요하거나 인증 토큰이 없는 경우 등)
        403: OpenApiResponse(
            description="권한 없는 사용자."
        ),  # 실패 응답(인증은 됐지만 접근 권한이 없음: 로그인 후 타 사용자의 정보를 수정하려는 경우 등)
    },
    examples=[  # 실제 사용 예시
        OpenApiExample(
            name="프로필 이미지 변경",
            value={"profile_img_url": "http://example.com/profile.jpg"},
            request_only=True,
        ),
        OpenApiExample(
            name="비밀번호 변경",
            value={"password": "newpassword"},
            request_only=True,
        ),
        OpenApiExample(
            name="닉네임 변경",
            value={"nickname": "newnicky"},  # 10글지 이내여야 함
            request_only=True,
        ),
        OpenApiExample(
            name="휴대폰 번호 변경",
            value={"phone_number": "01098765432", "verification_code": "654321"},
            request_only=True,
        ),
        OpenApiExample(
            name="여러 항목 동시 수정",
            value={
                "nickname": "upuser",
                "password": "strongpw-123",
                "phone_number": "01011112222",
                "verification_code": "112233",
            },
            request_only=True,
        ),
    ],
)

# 사용자 정보 수정
class UserInfoEditView(AuthenticatedAPIview):
    def patch(self, request: Request) -> Response:
        """
        현재 로그인한 사용자의 정보를 수정하는 API 뷰.
        로그인 필수. 휴대폰 번호 변경 시 인증 코드 검증 포함.
        """
        # 로그인한 사용자(User)를 서비스 코드로 넘겨 사용자 정보를 수정하는 서비스 생성
        user = cast(User, request.user)
        service = UserInfoEditService(user)

        try:
            updated_user = service.update_user_info(request.data)  # 서비스 호출
        except ValidationError as e:
            # ValidationError는 보통 detail에 오류 내용을 담고 있으므로, 만약 detail이 있다면 그것을 가져오고, 그렇지 않다면 str(e)를 반환한다
            detail = getattr(e, "detail", str(e))

            # 인증 코드 미입력
            if "휴대폰 번호 변경 시 인증 코드가 필요합니다." in str(detail):
                return Response({"detail": detail}, status=status.HTTP_401_UNAUTHORIZED)

            # 기타 오류들
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)

        # 수정 성공
        serializer = UserInfoSerializer(updated_user)
        return Response(
            {"message": "회원 정보가 정상적으로 수정되었습니다.", "user": serializer.data}, status=status.HTTP_200_OK
        )
