from functools import partial
from typing import Any, Dict

from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from apps.lectures.models.crawled_lectures import Lecture
from apps.users.models.user import User

from ...core.utils import S3Uploader
from ..models import RecruitmentImage
from ..models.recruitment_attachments import RecruitmentAttachment
from ..models.recruitments import Recruitment
from ..models.tags import Tag
from .attachments_serializers import RecruitmentAttachmentSerializer


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["id", "nickname"]


class TagSerializer(serializers.ModelSerializer[Tag]):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class LectureSerializer(serializers.ModelSerializer[Lecture]):
    class Meta:
        model = Lecture
        fields = [
            "title",
            "url_link",
            "instructor",
            "thumbnail_img_url",
            "original_price",  # 원래 가격
            "discount_price",  # 할인된 가격
        ]


class AdminRecruitmentListSerializer(serializers.ModelSerializer[Recruitment]):
    tags = TagSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()
    bookmark_count = serializers.IntegerField()

    class Meta:
        model = Recruitment
        fields = [
            "id",
            "uuid",
            "title",
            "tags",
            "close_at",
            "status",
            "views_count",
            "bookmark_count",
            "created_at",
            "updated_at",
        ]

    def get_status(self, obj: Recruitment) -> str:
        return "closed" if obj.is_closed else "recruiting"


class RecruitmentDetailSerializer(serializers.ModelSerializer[Recruitment]):
    author = UserSerializer(read_only=True)
    attachments = RecruitmentAttachmentSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    study_lectures = LectureSerializer(many=True, read_only=True, source="study_group.lectures.all")
    bookmark_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recruitment
        fields = [
            "id",
            "uuid",
            "author",
            "title",
            "content",
            "expected_headcount",
            "estimated_fee",
            "study_lectures",
            "tags",
            "attachments",
            "created_at",
            "updated_at",
            "close_at",
            "is_closed",
            "views_count",
            "bookmark_count",
        ]

    @staticmethod
    def get_bookmark_count(obj: Recruitment) -> int:
        return obj.bookmark_users.count()


class RecruitmentUpdateSerializer(serializers.ModelSerializer[Recruitment]):
    tags = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    attachments = RecruitmentAttachmentSerializer(many=True, required=False, write_only=True)
    images = serializers.ListField(child=serializers.URLField(), max_length=5, required=False, write_only=True)

    class Meta:
        model = Recruitment
        fields = [
            "title",
            "content",
            "expected_headcount",
            "estimated_fee",
            "tags",
            "close_at",
            "attachments",
            "images",
        ]

    @transaction.atomic
    def update(self, instance: Recruitment, validated_data: dict[str, Any]) -> Recruitment:
        tag_names = validated_data.pop("tags", [])
        attachments_data = validated_data.pop("attachments", [])
        images = validated_data.pop("images", [])

        if tag_names:
            tags_to_add = [Tag.objects.get_or_create(name=name)[0] for name in tag_names]
            instance.tags.set(tags_to_add)

        pre_attachment_urls = []
        if attachments_data:
            pre_attachment_urls = list(instance.attachments.values_list("file_url", flat=True))
            instance.attachments.all().delete()
            RecruitmentAttachment.objects.bulk_create(
                [RecruitmentAttachment(recruitment=instance, **item) for item in attachments_data]
            )

        pre_image_urls = []
        if images:
            pre_image_urls = list(instance.images.values_list("img_url", flat=True))
            instance.images.all().delete()
            RecruitmentImage.objects.bulk_create(
                [RecruitmentImage(recruitment=instance, img_url=url) for url in images]
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if pre_image_urls or pre_attachment_urls:
            transaction.on_commit(
                partial(self._cleanup_orphan_images_or_attachments, urls=pre_attachment_urls + pre_image_urls)
            )
        return instance

    def _cleanup_orphan_images_or_attachments(self, urls: list[str]) -> None:
        S3Uploader().delete_files(urls)


# 공고 작성에 사용(첨부파일 가공)
class AttachmentInputSerializer(serializers.Serializer[RecruitmentAttachment]):
    file_url = serializers.URLField(max_length=255)
    file_name = serializers.CharField(max_length=50)


# 공고 작성 시리얼라이저
class RecruitmentCreateOutputSerializer(serializers.ModelSerializer[Recruitment]):
    class Meta:
        model = Recruitment
        fields = ["uuid", "title"]


class RecruitmentCreateSerializer(serializers.ModelSerializer[Recruitment]):
    images = serializers.ListField(child=serializers.URLField(), max_length=5, required=False)
    attachments = AttachmentInputSerializer(many=True, required=False)
    tags = serializers.ListField(child=serializers.IntegerField(), required=False)
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Recruitment
        fields = [
            "author",
            "title",
            "content",
            "close_at",
            "expected_headcount",
            "study_group",
            "images",
            "attachments",
            "estimated_fee",
            "tags",
        ]
        extra_kwargs = {
            "images": {"write_only": True},
            "attachments": {"write_only": True},
            "estimated_fee": {"required": False},
            "tags": {"write_only": True},
        }

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # 첨부파일 제한
        attachments = data.get("attachments")
        if attachments and len(attachments) > 3:
            raise serializers.ValidationError({"attachments": "첨부 파일은 최대 3개까지 등록 가능합니다."})

        # 스터디그룹 상태 제한
        study_group = data.get("study_group")
        if study_group and study_group.status == "ENDED":
            raise serializers.ValidationError({"study_group": "종료된 스터디 그룹은 등록 불가능합니다."})

        return data

    def create(self, validated_data: Dict[str, Any]) -> Recruitment:
        images = validated_data.pop("images", None)
        attachments = validated_data.pop("attachments", None)
        tags = validated_data.pop("tags", None)

        # estimated_fee를 입력하지 않았다면 스터디그룹의 강의 비용을 합산해서 자동 등록
        if "estimated_fee" not in validated_data:
            study_group = validated_data["study_group"]
            total = study_group.lectures.aggregate(total=Sum("original_price"))["total"]
            if total is None:
                total = 0
            validated_data["estimated_fee"] = total

        # recruitment는 등록
        recm = Recruitment.objects.create(**validated_data)

        # 이미지 등록
        if images is not None:
            image_list = []
            for i in images:
                image_list.append(RecruitmentImage(recruitment=recm, img_url=i))
            RecruitmentImage.objects.bulk_create(image_list)

        # 첨부 파일 등록
        if attachments is not None:
            attachment_list = []
            for i in attachments:
                attachment_list.append(
                    RecruitmentAttachment(recruitment=recm, file_url=i["file_url"], file_name=i["file_name"])
                )
            RecruitmentAttachment.objects.bulk_create(attachment_list)

        if tags is not None:
            recm.tags.set(tags)

        return recm
