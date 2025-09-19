import re
from functools import partial
from typing import Any
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from apps.core.utils.s3_uploader import S3Uploader

from ..models.recruitment_attachments import RecruitmentAttachment
from ..models.recruitment_images import RecruitmentImage
from ..models.recruitments import Recruitment
from ..models.tags import Tag


def get_recruitment_detail(recruitment_uuid: UUID) -> Recruitment:
    try:
        recruitment = (
            Recruitment.objects.select_related("author")
            .prefetch_related("tags", "attachments", "images")
            .get(uuid=recruitment_uuid)
        )
        return recruitment
    except Recruitment.DoesNotExist:
        raise ObjectDoesNotExist("해당 공고를 찾을 수 없음.")


@transaction.atomic
def update_recruitment(instance: Recruitment, validated_data: dict[str, Any]) -> Recruitment:
    tag_names = validated_data.pop("tags", None)
    attachments_data = validated_data.pop("attachments", None)
    image_urls = validated_data.pop("images", None)
    new_content = validated_data.get("content", instance.content)

    for attr, value in validated_data.items():
        setattr(instance, attr, value)
    instance.save()

    if tag_names is not None:
        instance.tags.clear()
        tags_to_add = [Tag.objects.get_or_create(name=name)[0] for name in tag_names]
        instance.tags.add(*tags_to_add)

    if attachments_data is not None:
        instance.attachments.all().delete()
        RecruitmentAttachment.objects.bulk_create(
            [RecruitmentAttachment(recruitment=instance, **item) for item in attachments_data]
        )

    if image_urls is not None:
        instance.images.all().delete()
        RecruitmentImage.objects.bulk_create(
            [RecruitmentImage(recruitment=instance, img_url=url) for url in image_urls]
        )

    transaction.on_commit(partial(_cleanup_orphan_images, instance=instance, content=new_content))
    return instance


# 마크다운 본문에 존재치 않는 이미지를 s3과 db에서 제거
def _cleanup_orphan_images(instance: Recruitment, content: str) -> None:
    urls_in_content = set(re.findall(r"!\[.*?\]\((.*?)\)", content))
    all_image_urls = set(instance.images.values_list("img_url", flat=True))
    orphan_urls = all_image_urls - urls_in_content

    if orphan_urls:
        images_to_delete = instance.images.filter(img_url__in=orphan_urls)
        s3_uploader = S3Uploader()
        for image in images_to_delete:
            if ".com/" in image.img_url:
                s3_key = image.img_url.split(".com/")[-1]
                s3_uploader.delete_file(key=s3_key)
        images_to_delete.delete()
