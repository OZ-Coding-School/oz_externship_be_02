# lectures/urls.py
from django.urls import path
from apps.lectures.views.lecture_list import LectureListView # 클래스 기반 뷰를 import합니다.


app_name = "lectures"

urlpatterns = [
    path('list/', LectureListView.as_view(), name='lecture_list'),
]