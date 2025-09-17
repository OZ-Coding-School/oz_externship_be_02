from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.s3_uploader import S3Uploader


class RecruitmentFileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        file_obj = request.FILES.get("file", None)
        if not file_obj:
            return Response({"error": "업로드할 파일이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.DEBUG:
            s3_uploader = S3Uploader()
            result = s3_uploader.upload_file(file_obj)
            file_url = result.get("url")
        else:
            file_url = f"https://s3.mock-domain.com/attachments/{file_obj.name}"

        if file_url:
            return Response({"file_name": file_obj.name, "file_url": file_url}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "파일 업로드에 실패했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
