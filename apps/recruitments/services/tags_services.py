"""
태그(Tag)와 관련된 비즈니스 로직을 처리하는 서비스 레이어.
View에서 이 서비스를 호출하여 비즈니스 로직의 결과를 받아 사용한다.
"""

from apps.recruitments.models import Tag

"""
태그 생성 및 관리를 담당하는 서비스 클래스
"""


class TagService:

    # 새로운 태그 생성
    def create_tag(self, name: str) -> Tag:

        # 새로운 태그를 생성하고 반환한다.
        tag = Tag.objects.create(name=name)
        return tag
