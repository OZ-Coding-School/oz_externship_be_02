# apps/applications/applications_status_services.py

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.exceptions import NotFound

from apps.applications.models import Application
from apps.studies.models import StudyGroup


class ApplicationStatusService:
    """
    지원서 상태 변경 관련 서비스
    - 승인 / 거절 로직 담당
    """

    @staticmethod
    def get_application(application_id: int) -> Application:
        try:
            return Application.objects.select_related("user", "recruitment__author", "recruitment__study_group").get(
                id=application_id
            )
        except Application.DoesNotExist:
            raise NotFound("해당 지원 내역을 찾을 수 없습니다.")

    @staticmethod
    def approve(application: Application) -> Application:
        if application.status != Application.ApplicationStatus.PENDING:
            raise ValidationError("이미 처리된 지원서입니다.")

        if not application.recruitment:
            raise ValidationError("지원서에 연결된 공고가 없습니다.")

        with transaction.atomic():
            study_group = StudyGroup.objects.select_for_update().get(id=application.recruitment.study_group.id)
            expected_headcount = application.recruitment.expected_headcount

            if study_group.members.count() >= expected_headcount:
                raise ValidationError("스터디 모집 인원이 모두 찼습니다. 승인할 수 없습니다.")

            application.status = Application.ApplicationStatus.ACCEPTED
            application.save()
            study_group.members.add(application.user)

        return application

    @staticmethod
    def reject(application: Application) -> Application:
        if application.status != Application.ApplicationStatus.PENDING:
            raise ValidationError("이미 처리된 지원서입니다.")

        with transaction.atomic():
            application.status = Application.ApplicationStatus.REJECTED
            application.save()

        return application
