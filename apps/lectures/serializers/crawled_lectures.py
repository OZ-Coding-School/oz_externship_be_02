from rest_framework import serializers

from apps.lectures.models.crawled_lectures import Lecture


class LectureSerializer(serializers.ModelSerializer[Lecture]):
    class Meta:
        model = Lecture
        exclude = ("id",)
