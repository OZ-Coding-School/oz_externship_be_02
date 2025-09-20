from unittest.mock import patch
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.test import APIRequestFactory

from apps.core.exception_handlers import universal_exception_handler

class UniversalExceptionHandlerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.context = {"view": None, "request": self.factory.get("/dummy")}

    def test_detail_message(self):
        exc = AuthenticationFailed("인증 실패")
        resp = universal_exception_handler(exc, self.context)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.data, {"error": "인증 실패"})

    def test_non_field_errors_message(self):
        exc = ValidationError({"non_field_errors": ["잘못된 요청", "추가 메시지"]})
        resp = universal_exception_handler(exc, self.context)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data, {"error": "잘못된 요청, 추가 메시지"})

    def test_field_validation_errors(self):
        exc = ValidationError({"username": ["필수값입니다."], "age": ["숫자여야 합니다."]})
        resp = universal_exception_handler(exc, self.context)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # 조합된 문자열이 '필드: 메시지' 형태로 들어가야 함
        msg = resp.data["error"]
        self.assertIn("username: 필수값입니다.", msg)
        self.assertIn("age: 숫자여야 합니다.", msg)

    def test_field_validation_errors_when_value_is_str(self):
        exc = ValidationError({"username": "필수값입니다."})
        resp = universal_exception_handler(exc, self.context)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # 조합된 문자열이 '필드: 메시지' 형태로 들어가야 함
        msg = resp.data["error"]
        self.assertIn("username: 필수값입니다.", msg)

    def test_list_error(self):
        exc = ValidationError(["리스트 에러1", "리스트 에러2"])
        resp = universal_exception_handler(exc, self.context)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data, {"error": "리스트 에러1, 리스트 에러2"})

    # def test_single_error_message(self):
    #     exc = ValidationError("단순한 에러1")
    #     resp = universal_exception_handler(exc, self.context)
    #     self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(resp.data, {"error": "단순한 에러1"})

    @patch("apps.core.exception_handlers.drf_exception_handler", return_value=None)
    def test_unhandled_exception_returns_500(self, mock_handler):
        exc = RuntimeError("DB connection lost")
        resp = universal_exception_handler(exc, self.context)
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(resp.data, {"error": "서버 내부 오류가 발생했습니다."})