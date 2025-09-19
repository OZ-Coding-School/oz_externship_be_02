from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.s3_uploader import S3Uploader


class RecruitmentFileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        file_obj = request.FILES.get("file")
        if not file_obj or file_obj.size == 0:
            return Response({"error": "업로드할 파일이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            s3_uploader = S3Uploader()
            result = s3_uploader.upload_file(file_obj)
            file_url = result.get("url")

        except Exception as e:
            return Response({"error": f"파일 업로드 중 오류 발생: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not file_url:
            raise ValueError("S3 업로드 후 URL 가져오지 못함")

        return Response(
            {"file_name": file_obj.name, "file_url": file_url},
            status=status.HTTP_200_OK,
        )