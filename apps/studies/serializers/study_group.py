from datetime import datetime, timezone
from typing import Any, Dict

from rest_framework import serializers

from apps.studies.models import GroupMember, StudyGroup
from apps.users.models.user import User


class StudyGroupSerializer(serializers.ModelSerializer[StudyGroup]):
    """
    스터디 그룹 생성 Serializer"""

    class Meta:
        model = StudyGroup
        fields = ["name", "introduction", "max_headcount", "profile_img_url", "start_at", "end_at"]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        스터디 그룹 생성 시, 시작일, 종료일 조건 검증
        `serializer.is_valid()` 실행 시, 자동으로 검증 함수 호출.
        * 검증 실패
            - 종료일이 시작일 이전일 경우
            - 시작일이 과거일 경우
            - 스터디 기간이 5일 미만인 경우
        :param attrs: 유저가 입력한 데이터
        :return: 검증 완료된 데이터
        """
        # 유저 검증 (group_members에 리더 데이터 저장)
        request = self.context.get("request")
        if request is None or not hasattr(request, "user"):  # hasattr : 특정 속성을 객체가 가지고 있는지 확인
            raise serializers.ValidationError("유저 데이터가 존재하지 않습니다.")

        # 인원 수 검증
        if attrs["max_headcount"] > 10:
            raise serializers.ValidationError("인원 수 초과 되었습니다.")

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

    def create(self, validated_data: Dict[str, Any]) -> StudyGroup:
        """
        스터디 그룹 생성 시, GroupMember에 리더 멤버 등록
        :param validated_data: study_group 데이터
        :return:
        """  # 스터디 그룹 생성
        study_group = super().create(validated_data)

        # user data 가져오기
        user = self.context["request"].user  # 시리얼라이저에서 리퀘스트로 유저 데이터 접근

        if not user:
            raise serializers.ValidationError("유저 데이터가 존재하지 않습니다. 로그인 여부를 확인해주세요.")

            # 리더 멤버 생성
        GroupMember.objects.create(study_group=study_group, user=user, is_leader=True)

        return study_group


class StudyGroupLeaderSerializer(serializers.ModelSerializer[User]):
    """
    스터디 그룹 리더 데이터 관리하는 Serializer"""

    class Meta:
        model = User
        fields = ["uuid", "nickname"]


class CreateSuccessResponse(serializers.Serializer[Any]):
    """
    스터디 그룹 생성 성공시 응답 Serializer
    """

    uuid = serializers.UUIDField()  # 생성된 스터디 그룹 uuid
    name = serializers.CharField()  # 스터디 그룹 이름
    introduction = serializers.CharField()  # 스터디 그룹 소개
    profile_img_url = serializers.CharField(allow_null=True, allow_blank=True)  # 스터디 그룹 대표 이미지
    start_at = serializers.DateTimeField()  # 스터디 그룹 시작일
    end_at = serializers.DateTimeField()  # 스터디 그룹 종료일
    max_headcount = serializers.IntegerField()  # 스터디 그룹 최대 인원
    created_by = serializers.JSONField()  # 스터디 그룹 생성한 유저 데이터 (리더)
    created_at = serializers.DateTimeField()  # 스터디 그룹 생성일
