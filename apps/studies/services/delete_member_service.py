from rest_framework.exceptions import PermissionDenied

from apps.studies.models.study_groups import StudyGroup
from apps.users.models import User


class DeleteMemberService:
    """
    스터디 그룹 멤버 삭제 서비스
    그룹 탈퇴, 강퇴 기능 구현.
    """

    def __init__(self, group: StudyGroup, user: User) -> None:
        self.group = group
        self.target = user

    def check_leader(self) -> bool:
        """
        탈퇴, 강퇴 요청 시 해당되는 유저가 그룹 리더인지 체크
        """
        return self.group.members.through.objects.get(user=self.target, study_group=self.group).is_leader

    def groupmember_delete_service(self) -> None:
        """
        스터디 그룹 탈퇴 및 강퇴 기능
        """
        if self.check_leader():
            raise PermissionDenied("그룹 리더는 리더 위임 후 그룹을 탈퇴할 수 있습니다.")
        self.group.members.remove(self.target)
