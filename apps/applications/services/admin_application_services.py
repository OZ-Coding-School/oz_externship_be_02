from typing import Tuple

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.applications.models.applications import Application
from apps.users.models.user import User


def check_permission(user: User) -> bool:
    if user.is_staff or user.is_superuser:
        return True
    else:
        return False


def get_admin_application_list() -> QuerySet[Application]:
    queryset = Application.objects.all().order_by("-created_at")
    return queryset


def filter_status(queryset: QuerySet[Application], status: str) -> QuerySet[Application]:
    filtered_queryset = queryset.filter(status=status)
    return filtered_queryset


def get_admin_application_detail(application_id: int) -> Tuple[Application, int]:
    aply = get_object_or_404(Application, id=application_id)
    headcount = Application.objects.filter(
        recruitment=aply.recruitment, status=Application.ApplicationStatus.ACCEPTED
    ).count()
    return aply, headcount
