from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils import S3Uploader
from apps.recruitments.serializers.images_serializers import ImagePreUploadSerializer


class RecruitmentImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=ImagePreUploadSerializer,
        responses={200: {"image_url": str}},
        description="S3에 이미지를 업로드하고 URL을 반환합니다.",
        tags=["Recruitment Images"],
    )
    def post(self, request: Request) -> Response:
        serializer = ImagePreUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload_image = serializer.validated_data.get("image")
        try:
            s3_uploader = S3Uploader()
            result = s3_uploader.upload_file(upload_image)
            image_url = result.get("url")

            return Response({"image_url": image_url}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"이미지 업로드 중 오류 발생: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
