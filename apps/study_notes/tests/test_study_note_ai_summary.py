from datetime import datetime
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from apps.studies.models import StudyGroup
from apps.study_notes.services.study_note_ai_summary import generate_study_summary
from apps.study_notes.services.study_notes_services import StudyNoteService
from apps.users.models.user import User


class StudyNoteAITestCase(TestCase):
    user: User
    other_user: User
    study_group: StudyGroup
    valid_note_content: str

    @classmethod
    def setUpTestData(cls) -> None:
        # 테스트 유저 생성
        cls.user = User.objects.create_user(
            email="junhyuk@example.com",
            password="test123",
            name="준혁",
            nickname="junhyuk",
            phone_number="01012345678",
            gender="남성",
            birthday="2000-01-01",
        )

        cls.other_user = User.objects.create_user(
            email="other@example.com",
            password="test123",
            name="타인",
            nickname="other",
            phone_number="01087654321",
            gender="남성",
            birthday="1990-01-01",
        )

        # 테스트 스터디 그룹 생성
        cls.study_group = StudyGroup.objects.create(
            name="AI 스터디",
            max_headcount=5,
            start_at=timezone.make_aware(datetime(2025, 9, 16, 12, 0, 0)),
            end_at=timezone.make_aware(datetime(2025, 9, 30, 12, 0, 0)),
        )
        cls.study_group.members.add(cls.user)

        # 정상 노트 데이터
        cls.valid_note_content = """
        오늘 이미지 및 파일 업로드를 위해 S3 업로더를 만들고 API를 따로 만들어 업로드 후 URL을 반환 받아 본문에 넣어 보내는 로직을 작성했다.
        그리고 업로드 과정에 생기는 고아객체를 처리하는 로직도 만들었다.
        """

    @patch("apps.study_notes.services.study_note_ai_summary.GOOGLE_API_KEY", "fake-api-key-for-test")
    @patch("apps.study_notes.services.study_note_ai_summary.genai.GenerativeModel")
    def test_normal_creation_with_mocked_ai(self, mock_model_class: Mock) -> None:
        """AI 호출을 mock 처리해서 노트 생성 테스트"""
        service = StudyNoteService()

        # mock 설정: 정상 텍스트 반환
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "요약된 AI 내용"
        mock_response.candidates = None
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        # 테스트용 파일 객체 생성
        image1 = SimpleUploadedFile("test1.png", b"image_content", content_type="image/png")
        image2 = SimpleUploadedFile("test2.png", b"image_content", content_type="image/png")
        attachment1 = SimpleUploadedFile("file1.pdf", b"file_content", content_type="application/pdf")

        note = service.create_study_note(
            author=self.user,
            study_group=self.study_group,
            title="정상 생성 테스트",
            content=self.valid_note_content,
            images=[image1, image2],
            attachments=[attachment1],
        )

        # 검증
        self.assertEqual(note.ai_summary, "요약된 AI 내용")
        self.assertEqual(note.images.count(), 2)
        self.assertEqual(note.attachments.count(), 1)

    @patch("apps.study_notes.services.study_note_ai_summary.GOOGLE_API_KEY", "fake-api-key-for-test")
    @patch("apps.study_notes.services.study_note_ai_summary.genai.GenerativeModel")
    def test_candidates_parts(self, mock_model_class: Mock) -> None:
        """response.text 없고 candidates.parts(text가 없을 때 여러 후보) 있는 경우"""
        part1 = Mock(text="부분1")
        part2 = Mock(text="부분2")
        candidate = Mock()
        candidate.content.parts = [part1, part2]

        mock_model = Mock()
        mock_model.generate_content.return_value = Mock(text=None, candidates=[candidate])
        mock_model_class.return_value = mock_model

        result = generate_study_summary("내용", "준혁", "2025-09-18")
        self.assertEqual(result, "부분1\n부분2")

    @patch("apps.study_notes.services.study_note_ai_summary.GOOGLE_API_KEY", "fake-api-key-for-test")
    @patch("apps.study_notes.services.study_note_ai_summary.genai.GenerativeModel")
    def test_exception(self, mock_model_class: Mock) -> None:
        """generate_content 호출 시 예외 발생"""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("모델 오류")
        mock_model_class.return_value = mock_model

        result = generate_study_summary("내용", "준혁", "2025-09-18")
        self.assertEqual(result, "AI 요약 생성 실패")
