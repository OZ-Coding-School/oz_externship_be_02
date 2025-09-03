from rest_framework.views import APIView
from rest_framework.response import Response
from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.serializers.crawled_lecture import LectureSerializer

class LectureListView(APIView):

    serializer_class = LectureSerializer

    def get(self, request):
        lectures = Lecture.objects.all()
        serializer = LectureSerializer(lectures, many=True)
        return Response(serializer.data)