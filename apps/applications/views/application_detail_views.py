from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.applications_permissions import (
    IsApplicantOrRecruiter,
    IsRecruiterOnly,
)
from apps.applications.models import Application
from apps.applications.serializers.application_detail_serializers import (
    ApplicationDetailSerializer,
)
from apps.applications.services.application_status_services import (
    ApplicationStatusService,
)
from drf_spectacular.utils import extend_schema, OpenApiResponse


class ApplicationDetailView(APIView):
    permission_classes = [IsApplicantOrRecruiter]
    @extend_schema(
        responses={
            200: ApplicationDetailSerializer,
            403: OpenApiResponse(description="권한 없음"),
            404: OpenApiResponse(description="지원서 없음"),
            500: OpenApiResponse(description="서버 에러"),
        },
    )
    def get(self, request: Request, application_id: int) -> Response:
        try:
            try:
                application = Application.objects.select_related("user", "recruitment__author").get(id=application_id)
            except Application.DoesNotExist:
                raise NotFound("해당 지원 내역을 찾을 수 없습니다.")

            self.check_object_permissions(request, application)

        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        serializer = ApplicationDetailSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    summary="지원서 승인",
    responses={
        200: ApplicationDetailSerializer,
        400: OpenApiResponse(description="잘못된 요청"),
        403: OpenApiResponse(description="권한 없음"),
        404: OpenApiResponse(description="지원서 없음"),
        500: OpenApiResponse(description="서버 에러"),
    },
)

class ApplicationStatusBaseView(APIView):
    permission_classes = [IsRecruiterOnly]
    action: str = ""

    def patch(self, request: Request, application_id: int) -> Response:
        try:
            application = ApplicationStatusService.get_application(application_id)
            self.check_object_permissions(request, application)

            if self.action == "approve":
                application = ApplicationStatusService.approve(application)
            elif self.action == "reject":
                application = ApplicationStatusService.reject(application)
            else:
                raise ValidationError("Invalid action")

        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": f"처리 중 오류가 발생했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ApplicationDetailSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    summary="지원서 승인",
    responses={
        200: ApplicationDetailSerializer,
        400: OpenApiResponse(description="잘못된 요청"),
        403: OpenApiResponse(description="권한 없음"),
        404: OpenApiResponse(description="지원서 없음"),
        500: OpenApiResponse(description="서버 에러"),
    },
)
class ApplicationApproveView(ApplicationStatusBaseView):
    action = "approve"

@extend_schema(
    summary="지원서 거절",
    responses={
        200: ApplicationDetailSerializer,
        400: OpenApiResponse(description="잘못된 요청"),
        403: OpenApiResponse(description="권한 없음"),
        404: OpenApiResponse(description="지원서 없음"),
        500: OpenApiResponse(description="서버 에러"),
    },
)
class ApplicationRejectView(ApplicationStatusBaseView):
    action = "reject"
