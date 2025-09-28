from apps.applications.models.applications import Application
from apps.users.models.user import User


def get_my_detail_aply(user: User, application_id: int) -> Application:
    try:
        aply = Application.objects.get(user=user, id=application_id)
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
