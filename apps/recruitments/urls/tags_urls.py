from django.urls import path

from ..views.tags_views import TagAPIView

urlpatterns = [
    # GET, POST 모두 동일한 URL을 사용한다.
    # .as_view() 메서드는 클래스 기반 뷰를 URL에 연결할 때 사용하는 표준 방식이다.
    path("/tags", TagAPIView.as_view(), name="tag-list"),
]
