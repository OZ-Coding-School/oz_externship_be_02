from typing import Any, Dict

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.core.utils import S3Uploader
from apps.lectures.models import Lecture
from apps.studies.models import GroupMember, StudyGroup, StudyLecture


class StudyGroupCreateUpdateSerializer(serializers.ModelSerializer[StudyGroup]):
    """
    스터디 그룹 Serializer
    """

    lectures = serializers.PrimaryKeyRelatedField(many=True, queryset=Lecture.objects.all(), required=False)
    profile_img = serializers.ImageField(required=False, write_only=True)
    max_headcount = serializers.IntegerField(max_value=10, error_messages={"max_value": "인원 수 초과 되었습니다."})

    class Meta:
        model = StudyGroup
        fields = [
            "uuid",
            "name",  # 스터디 그룹명
            "introduction",  # 스터디 소개글
            "max_headcount",  # 최대 인원 수
            "profile_img_url",  # 스터디 그룹의 썸네일(프로필) 이미지
            "profile_img",
            "start_at",  # 스터디 시작일
            "end_at",  # 스터디 종료일
            "lectures",  # 스터디 그룹에서 수강할 강의
            "created_at",
        ]
        extra_kwargs = {
            "uuid": {"read_only": True},
        }

    def validate_lectures(self, value: list[int]) -> list[int]:
        if len(value) > 5:
            raise serializers.ValidationError({"lectures": "강의는 최대 5개까지 등록 가능합니다."})
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        **시작일 / 종료일 관련 검증 로직**
        - 종료일은 시작일 이후여야 한다.
        - 시작일은 오늘 / 오늘 이후여야한다.
        - 스터디 기간은 최소 5일.
        :param attrs: 유저가 입력한 시작일 / 종료일
        """
        instance = getattr(self, "instance", None)
        # 날짜 검증
        start_at = attrs.get("start_at", getattr(instance, "start_at", None))
        end_at = attrs.get("end_at", getattr(instance, "end_at", None))

        if start_at is not None:
            # 시작일이 과거일 경우
            if start_at < timezone.now():
                raise serializers.ValidationError("스터디 시작일이 과거일 수 없습니다.")
        if start_at is not None and end_at is not None:
            # 종료일이 시작일 이전일 경우
            if start_at > end_at:
                raise serializers.ValidationError("스터디 종료일이 시작일보다 이전일 수 없습니다.")
            # 스터디 기간이 5일 미만인 경우
            if (end_at - start_at).days < 4:
                raise serializers.ValidationError("스터디 종료 날짜는 시작날 기준 최소 5일 이후여야 합니다. ")
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Any:
        """
        스터디 그룹 생성과 함께 GroupMember에 리더 멤버 등록
        :param validated_data: study_group 데이터
        :return: study_group data
        """
        user = validated_data.pop("user")  # 유저 데이터만 추출

        lectures = validated_data.pop("lectures")  # 선택 강의 데이터만 추출

        if "profile_img" in validated_data:  # 이미지 데이터가 있을 경우에만 실행
            img = validated_data.pop("profile_img")  # 이미지 데이터 추출
            s3_uploader = S3Uploader()  # S3 업로드 객체화
            profile_img_url = s3_uploader.upload_file(file=img)  # S3에 이미지 업로드
            validated_data["profile_img_url"] = profile_img_url.get("url")  # profile img url 저장

        with transaction.atomic():  # 하나의 작업으로 묶음, 실패 시 롤백
            study_group = StudyGroup.objects.create(**validated_data)  # 스터디 그룹 관련 데이터들을 생성.
            study_lectures = [
                StudyLecture(lecture=i, study_group=study_group) for i in lectures
            ]  # 선택 강의 데이터, Many to Many 연결용 객체 리스트
            StudyLecture.objects.bulk_create(study_lectures)  # bulk insert로 중간 테이블에 데이터 저장
            GroupMember.objects.create(study_group=study_group, is_leader=True, user=user)  # 그룹 멤버에 leader로 저장.
            study_group.refresh_from_db()  # DB 객체 캐시 동기화, bulk_create 추가된 Many to Many 반영
        return study_group

    def update(self, instance: StudyGroup, validated_data: Dict[str, Any]) -> Any:
        """
        등록된 스터디 그룹을 수정.
        :param instance: 기존 객체
        :param validated_data: 검증 끝난 데이터
        :return:
        """
        if "profile_img" in validated_data:  # 이미지 데이터가 있을 경우에만 실행
            img = validated_data.pop("profile_img")
            s3_uploader = S3Uploader()
            profile_img_url = s3_uploader.upload_file(file=img)
            validated_data["profile_img_url"] = profile_img_url.get("url")

        lectures = validated_data.pop("lectures", None)  # 강의 데이터가 있을 경우에만 데이터 추출, 없으면 None

        with transaction.atomic():  # 하나의 작업으로 묶음, 실패 시 롤백
            instance = super().update(instance, validated_data)  # 일반 필드 업데이트 및 save()처리.

            if lectures is not None:
                instance.lectures.set(lectures)  # Many to Many는 별도로 처리.

        return instance

    def to_representation(self, instance: StudyGroup) -> dict[str, Any]:
        ret = super().to_representation(instance)
        ret["lectures"] = list(instance.lectures.values_list("id", flat=True))
        return ret
