from typing import Optional

from rest_framework.exceptions import PermissionDenied

from apps.applications.models.applications import Application
from apps.users.models.user import User


def get_my_detail_aply(user: User, application_id: int) -> Optional[Application]:
    try:
        aply = Application.objects.get(id=application_id)
        if aply.user != user:
            raise PermissionDenied
    except Application.DoesNotExist:
        aply = None
    return aply


def cancel_my_aply(user: User, application_id: int) -> bool:
    aply = get_my_detail_aply(user, application_id)
    if aply is None or aply.status != Application.ApplicationStatus.PENDING:
        return False
    else:
        aply.status = Application.ApplicationStatus.CANCELED
        aply.save()
        return True
