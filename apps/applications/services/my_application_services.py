from apps.applications.models.applications import Application

def get_my_detail_aply(user, application_id):
    queryset=Application.objects.get(user=user, id=application_id)
    return queryset

def cancel_my_aply(user, application_id):
    aply=get_my_detail_aply(user, application_id)
    if aply.status==Application.ApplicationStatus.PENDING:
        aply.status=Application.ApplicationStatus.CANCELED
        aply.save()
        return True
    else:
        return False