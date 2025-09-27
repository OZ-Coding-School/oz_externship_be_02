from apps.applications.models.applications import Application

def get_my_detail_aply(user, application_id):
    queryset=Application.objects.get(user=user, id=application_id)
    return queryset