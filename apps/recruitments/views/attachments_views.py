from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.s3_uploader import S3Uploader
from apps.recruitments.serializers.attachments_serializers import (
    AttachmentPreUploadSerializer,
)


class RecruitmentFileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=AttachmentPreUploadSerializer,
        responses={200: {"file_url": str}},
        description="S3에 파일을 업로드하고 URL을 반환합니다.",
        tags=["Recruitment Files"],
    )
    def post(self, request: Request) -> Response:
        serializer = AttachmentPreUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload_file = serializer.validated_data.get("file")
        try:
            s3_uploader = S3Uploader()
            result = s3_uploader.upload_file(upload_file)
            file_url = result.get("url")

            return Response({"file_url": file_url}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"파일 업로드 중 오류 발생: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
