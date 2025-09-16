from rest_framework import serializers
from .models import ChatMessage
from apps.studies.models import StudyGroup # study groups 이름을 가지고 오기 위해 import
from apps.users.models import User # user의 이름을 가지고 오기 위해서 import 했음

class ChatMessageSerializer(serializers.ModelSerializer[ChatMessage]):
    study_group_name = serializers.SerializerMethodField(read_only=True) # study group 이름
    # last_message = serializers.SerializerMethodField(read_only=True) # 가장 최근에 온 메세지(content) # 상황에 따라서 view에서 처리 (N+1 문제 방지)
    is_read = serializers.SerializerMethodField(read_only=True) # 읽음 여부

    class Meta:
        model = ChatMessage
        fields = ["study_group_name", "updated_at", "created_at", "is_read", "content"]


    def get_study_group_name(self, obj): # 스터디 그룹 이름 조회
        return obj.study_group.name

    def get_is_read(self, obj): # 읽음처리 어떻게 할지 의논해야함
        return False

