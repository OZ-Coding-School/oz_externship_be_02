import logging
from typing import Any, cast

from rest_framework import status, serializers
from rest_framework.exceptions import ValidationError, APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def universal_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """
    DRF에서 발생하는 모든 예외를 {"error": "메시지"} 형태로 통일하는 핸들러
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        logger.error(f"Unhandled exception occurred: {exc}", exc_info=True)
        return Response({"error": "서버 내부 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 에러 메시지 추출 - 순서가 중요함
    if isinstance(response.data, dict):
        if "detail" in response.data:
            # 단순한 detail 메시지 (인증 실패 등)
            error_message = str(response.data["detail"])
        elif "non_field_errors" in response.data:
            # 시리얼라이저의 non_field_errors
            error_message = ", ".join([str(err) for err in response.data["non_field_errors"]])
        else:
            # 여러 필드의 validation 에러를 읽기 쉽게 조합
            error_parts = []
            for field, errors in response.data.items():
                if isinstance(errors, list):
                    error_parts.append(f"{field}: {', '.join([str(err) for err in errors])}")
                else:
                    error_parts.append(f"{field}: {str(errors)}")
            error_message = "; ".join(error_parts)
    elif isinstance(response.data, list):
        error_message = ", ".join([str(err) for err in response.data])
    else:
        error_message = str(response.data)

    return Response({"error": error_message}, status=response.status_code)
