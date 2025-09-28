from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.applications.serializers.application_detail_serializers import MyApplicationDetailSerializer
from apps.applications.services.my_application_services import get_my_detail_aply, cancel_my_aply
from rest_framework.permissions import IsAuthenticated

class MyDetailApplicationView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get(self, request, application_id):
        my_aply=get_my_detail_aply(request.user, application_id)
        serializer = MyApplicationDetailSerializer(my_aply)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, application_id):
        result=cancel_my_aply(request.user, application_id)
        if result:
            return Response({"success": "지원을 취소했습니다."}, status=status.HTTP_200_OK)
        return Response({"fail":"대기 중 지원만 취소 가능합니다."}, status=status.HTTP_404_NOT_FOUND)