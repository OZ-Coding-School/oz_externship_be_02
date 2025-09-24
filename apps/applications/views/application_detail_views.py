from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.applications_permissions import IsApplicantOrRecruiter
from apps.applications.models import Application
from apps.applications.serializers.application_detail_serializers import (
    ApplicationDetailSerializer,
)


class ApplicationDetailView(APIView):
    permission_classes = [IsApplicantOrRecruiter]

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
