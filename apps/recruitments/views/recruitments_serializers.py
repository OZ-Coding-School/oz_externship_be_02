from rest_framework import serializers
from apps.users.models.user import User

from apps.recruitments.models import Recruitment
from apps.recruitments.models.tags import Tag
from apps.recruitments.models.recruitment_attachments import recruitment_attachments

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class RecruitmentAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = recruitment_attachments
        fields = ['id', 'file_url', 'description']