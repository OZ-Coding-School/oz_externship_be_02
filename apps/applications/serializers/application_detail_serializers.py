from rest_framework import serializers

from apps.applications.models import Application


class ApplicationDetailSerializer(serializers.ModelSerializer[Application]):
    uuid = serializers.IntegerField(source="id", read_only=True)
    title = serializers.CharField(source="recruitment.title", read_only=True)
    applied_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Application
        fields = [
            "uuid",
            "title",
            "status",
            "applied_at",
            "self_introduction",
            "motivation",
            "objective",
            "available_time",
            "has_study_experience",
            "study_experience",
        ]
