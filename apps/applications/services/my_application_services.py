from apps.applications.models.applications import Application
from apps.users.models.user import User


def get_my_detail_aply(user: User, application_id: int) -> Application:
    aply = Application.objects.get(user=user, id=application_id)
    return aply


def cancel_my_aply(user: User, application_id: int) -> bool:
    aply = get_my_detail_aply(user, application_id)
    if aply.status == Application.ApplicationStatus.PENDING:
        aply.status = Application.ApplicationStatus.CANCELED
        aply.save()
        return True
    else:
        return False
