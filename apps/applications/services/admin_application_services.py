from django.db.models import QuerySet
from apps.applications.models.applications import Application

def check_permission(user)->bool:
    if user.is_staff or user.is_superuser:
        return True
    else:
        return False

def get_admin_application_list()->QuerySet:
    queryset = Application.objects.all().order_by('-created_at')
    return queryset

def filter_status(queryset, status)->QuerySet:
    filtered_queryset = queryset.filter(status=status)
    return filtered_queryset