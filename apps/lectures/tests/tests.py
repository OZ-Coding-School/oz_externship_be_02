from django.test import TestCase
from unittest.mock import patch
from lectures.models import Lecture

class LectureTestCase(TestCase):
    def setUp(self):
        # Given
        self.lecture_id = 1
        self.lecture = Lecture.objects.create(
            id=self.lecture_id,
            title="테스트 강의",
            instructor="코딩 파트너",
            average_rating=5.0,
            thumbnail_img_url="http://example.com/img.jpg",
            difficulty="초급",
            original_price=10000,
            discount_price=5000,
            platform="유데미",
            url_link="http://example.com/lecture/1"
        )
    def test_lecture_creation(self):
        retrieved_lecture = Lecture.objects.get(id=self.lecture_id)
        self.assertEqual(retrieved_lecture.title, "테스트 강의")
        self.assertEqual(retrieved_lecture.instructor, "코딩 파트너")
        self.assertEqual(retrieved_lecture.original_price, 10000)

    def test_lecture_title_is_correct(self):
        retrieved_lecture = Lecture.objects.get(title="테스트 강의")
        self.assertEqual(retrieved_lecture.title, self.lecture.title)
    # When


    #
    # def test_get_lecture_list(self):
    #
    #     # Then
