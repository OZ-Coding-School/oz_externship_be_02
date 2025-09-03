from rest_framework import serializers


# 요청 데이터 (lecture_id만 필요)
class BookmarkToggleRequestSerializer(serializers.Serializer):
    lecture_id = serializers.IntegerField()


# 응답 데이터 (lecture_id랑 북마크 여부만 리턴)
class BookmarkToggleResponseSerializer(serializers.Serializer):
    lecture_id = serializers.IntegerField()
    bookmarked = serializers.BooleanField()
