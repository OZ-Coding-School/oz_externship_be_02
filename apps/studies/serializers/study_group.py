from datetime import datetime, timezone
from typing import Any, Dict

from django.db import transaction
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from apps.studies.models import GroupMember, StudyGroup
from apps.users.models.user import User


class StudyGroupSerializer(serializers.ModelSerializer[StudyGroup]):
    """
    스터디 그룹 Serializer
    """

    class Meta:
        model = StudyGroup
        fields = ["name", "introduction", "max_headcount", "profile_img_url", "start_at", "end_at"]

    def validate_max_headcount(self, value: int) -> int:
        """
        스터디 그룹 생성 시, 시작일, 종료일 조건 검증 -> `serializer.is_valid()` 실행 시, 자동으로 검증 함수 호출.
        **인원 수 검증 로직**
        :param vslur: 유저가 입력한 스터디 그룹 최대 인원 수
        """
        # 인원 수 검증
        if value > 10:
            raise serializers.ValidationError("인원 수 초과 되었습니다.")
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        **시작일 / 종료일 관련 검증 로직**
        - 종료일은 시작일 이후여야 한다.
        - 시작일은 오늘 / 오늘 이후여야한다.
        - 스터디 기간은 최소 5일.
        :param attrs: 유저가 입력한 시작일 / 종료일
        """
        # 날짜 검증
        start_at = attrs["start_at"]
        end_at = attrs["end_at"]

        # 종료일이 시작일 이전일 경우
        if start_at > end_at:
            raise serializers.ValidationError("스터디 종료일이 시작일보다 이전일 수 없습니다.")
        # 시작일이 과거일 경우
        if start_at < datetime.now(tz=timezone.utc):
            raise serializers.ValidationError("스터디 시작일이 과거일 수 없습니다.")
        # 스터디 기간이 5일 미만인 경우
        if (end_at - start_at).days < 4:
            raise serializers.ValidationError("스터디 종료 날짜는 시작날 기준 최소 5일 이후여야 합니다. ")
        return attrs


class StudyCreateSerializer(serializers.ModelSerializer[GroupMember]):
    """
    스터디 그룹 멤버 Serializer
    """

    study_group = StudyGroupSerializer()
    user: PrimaryKeyRelatedField[User] = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = GroupMember
        fields = ["study_group", "user", "is_leader"]

    def create(self, validated_data: Dict[str, Any]) -> GroupMember:
        """
        스터디 그룹 생성 시, GroupMember에 리더 멤버 등록
        :param validated_data: study_group 데이터
        :param user:
        :return:
        """
        with transaction.atomic():
            study_group_data = validated_data.pop("study_group")
            study_group = StudyGroup.objects.create(**study_group_data)

            leader = GroupMember.objects.create(study_group=study_group, is_leader=True, **validated_data)
        return leader


class CreateSuccessResponse(serializers.ModelSerializer[GroupMember]):
    class Meta:
        # model = StudyGroup
        # fields = ['uuid', 'name', 'introduction', 'profile_img_url', 'start_at', 'end_at', 'max_headcount', 'created_at']
        model = GroupMember
        fields = ["user", "study_group"]

    def to_representation(self, obj: GroupMember) -> Dict[str, Any]:
        return {
            "uuid": str(obj.study_group.uuid),
            "name": obj.study_group.name,
            "introduction": obj.study_group.introduction,
            "profile_img_url": obj.study_group.profile_img_url,
            "start_at": obj.study_group.start_at.isoformat(),
            "end_at": obj.study_group.end_at.isoformat(),
            "max_headcount": obj.study_group.max_headcount,
            "created_by": {
                "uuid": str(obj.user.uuid),
                "nickname": obj.user.nickname,
            },
        }
