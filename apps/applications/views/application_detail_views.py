from typing import cast

from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.applications_permissions import IsApplicantOrRecruiter
from apps.applications.serializers.application_detail_serializers import (
    ApplicationDetailSerializer,
)
from apps.applications.services.application_detail_services import (
    ApplicationDetailService,
)
from apps.users.models import User


class ApplicationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsApplicantOrRecruiter]

    def get(self, request: Request, application_id: int) -> Response:
        try:
            user = cast(User, request.user)
            application = ApplicationDetailService.get_application_detail(application_id=application_id, user=user)

            self.check_object_permissions(request, application)

        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        serializer = ApplicationDetailSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)
