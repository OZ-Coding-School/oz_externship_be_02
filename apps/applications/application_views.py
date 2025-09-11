from typing import cast
from uuid import UUID

from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.serializers.application_serializers import (
    ApplicationCreateSerializer,
)
from apps.recruitments.models import Recruitment
from apps.users.models import User

from .models import Application


class ApplicationAPIView(APIView):
    """
    APIView를 상속받아 HTTP 메서드(post)에 따른 로직을 직접 구현.
    전체 작업 흐름을 조율하는 Orchestrator 역할을 한다.
    """

    # IsAuthenticated: 요청을 보낸 사용자가 로그인 상태인지(인증되었는지) 확인.
    # 인증되지 않은 사용자의 요청은 401 Unauthorized 에러를 반환하며 post 메서드가 실행되지 않는다.
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, recruitment_uuid: UUID) -> Response:
        # 지원서 생성 요청(POST)을 처리.

        # --- 1. 공고 객체 조회 --- #
        # URL로 받은 recruitment_uuid를 사용해 지원 대상 공고 객체를 조회.
        # 만약 해당 uuid의 공고가 없으면 DoesNotExist 예외가 발생하며, 이는 API의 핵심 로직을
        # 수행하기 위한 기본 조건이므로, 즉시 404 Not Found 응답을 반환하고 처리를 중단한다.
        try:
            recruitment = Recruitment.objects.get(uuid=recruitment_uuid)
        except Recruitment.DoesNotExist:
            return Response(
                {"error_code": "RECRUITMENT_NOT_FOUND", "message": "해당 스터디 공고를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # --- 2. 데이터 유효성 검사 --- #
        # 클라이언트가 보낸 데이터를 ApplicationCreateSerializer에 넘겨 유효성을 검사.
        # is_valid()는 모델 필드의 기본 제약조건과 Serializer에 직접 정의한 validate 메서드를 모두 실행한다.
        serializer = ApplicationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            # 유효성 검사에 실패하면, 어떤 필드가 왜 실패했는지에 대한 정보가 serializer.errors에 담긴다.
            # 이 정보를 400 Bad Request 응답에 담아 클라이언트에게 전달한다.
            return Response(
                {"error_code": "INVALID_INPUT", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        # --- 3. 핵심 로직(지원서 생성) 호출 및 결과 처리 --- #
        # 모든 검증을 통과하면, View가 직접 DB 로직을 처리하지 않고 Manager에게 로직을 위임한다.
        # user, recruitment 객체와 유효성 검사를 마친 데이터(serializer.validated_data)를 전달한다.
        try:
            # IsAuthenticated 권한 클래스에 의해 이 시점의 request.user는 항상 User 객체임이 보장된다..
            user = cast(User, request.user)
            application = Application.objects.create_application(
                user=user, recruitment=recruitment, **serializer.validated_data
            )
        # Manager의 create_application 메서드에서 중복 지원 시 IntegrityError를 발생시키기로 약속했으므로,
        # 이 예외를 받아서, API 명세에 맞는 403 Forbidden 응답을 생성하여 반환한다.
        except IntegrityError as e:
            return Response(
                {"error_code": "DUPLICATE_APPLICATION", "message": str(e)}, status=status.HTTP_403_FORBIDDEN
            )

        # 모든 과정이 성공적으로 끝나면, 생성된 지원서의 ID를 포함하여 201 Created 응답을 반환한다.
        return Response(
            {"application_id": application.id, "message": "스터디 공고 참여 신청 성공"}, status=status.HTTP_201_CREATED
        )
