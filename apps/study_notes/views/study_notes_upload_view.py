from typing import Dict, List, Optional, Union

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_notes.services.study_notes_services import StudyNoteService


class StudyNoteUploadView(APIView):
    """
    이미지/파일 업로드 전용 API
    - S3 업로드 후 URL 반환
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    service_class = StudyNoteService

    def get_service(self) -> Optional[StudyNoteService]:
        return self.service_class(s3_uploader=getattr(self, "s3_uploader", None))

    @extend_schema(
        tags=["스터디 기록 (StudyNotes)"],
        summary="스터디 기록 이미지/첨부 업로드",
        description="글 작성 전에 이미지/첨부파일을 업로드하여 S3 URL을 받습니다.",
        request=None,
        responses={200: {"type": "object"}},
    )
    def post(self, request: Request, group_uuid:str) -> Response:
        service = self.get_service()
        assert service is not None

        files_to_upload = {
            "images": request.FILES.getlist("images_file"),
            "attachments": request.FILES.getlist("attachments_file"),
        }

        result: Dict[str, List[Union[str, Dict[str, str]]]] = {"images": [], "attachments": []}

        # 반복 최소화: 한 번의 for문으로 처리
        for key, files in files_to_upload.items():
            for f in files:
                try:
                    s3_data = service.s3.upload_file(f)
                    if key == "images":
                        result["images"].append(s3_data["url"])
                    else:  # attachments
                        result["attachments"].append({"file_name": f.name, "url": s3_data["url"]})
                except Exception as e:
                    import logging

                    logger = logging.getLogger("django")
                    logger.warning(f"S3 업로드 실패: {f.name}, error: {e}")
                    # 실패 파일은 결과에서 제외하고 로깅만

        return Response(result, status=status.HTTP_200_OK)
