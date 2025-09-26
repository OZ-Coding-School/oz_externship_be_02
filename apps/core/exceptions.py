from rest_framework import status
from rest_framework.exceptions import APIException


class ConflictException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = '이미 존재하는 값입니다.'
    default_code = 'conflict'