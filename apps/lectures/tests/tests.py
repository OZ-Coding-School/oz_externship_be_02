from django.test import TestCase, Client
from unittest.mock import patch
from apps.lectures.models.crawled_lectures import Lecture
import uuid
from django.urls import reverse

class LectureTestCase(TestCase):
    def setUp(self):
        # Given
        self.client = Client()
        self.list_url = reverse('lectures:lecture_list')
        self.lecture1 = Lecture.objects.create(
            id=1,
            uuid=uuid.uuid4(),
            title="테스트 강의",
            instructor="코딩 파트너",
            average_rating=5.0,
            duration=100,
            difficulty="초급",
            description="PARKCODING",
            platform="유데미",
            original_price=10000,
            discount_price=5000,
            url_link="http://example.com/lecture/1",
            thumbnail_img_url="http://example.com/img.jpg",
        )
        self.lecture2 = Lecture.objects.create(
            id=2,
            uuid=uuid.uuid4(),
            title="테스트 강의2",
            instructor="코딩 파트너2",
            average_rating=4.0,
            duration=80,
            difficulty="초급",
            description="NOTPARKCODING",
            platform="인프런",
            original_price=20000,
            discount_price=1000,
            url_link="http://example.com/lecture/2",
            thumbnail_img_url="http://example.com/img2.jpg",
        )

    def test_lecture_list_api(self):
        # When
        response = self.client.get(self.list_url)

        # Then
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(len(response_data), 2)

        first_lecture_data = response_data[0]
        self.assertEqual(first_lecture_data['title'], self.lecture1.title)
        self.assertEqual(first_lecture_data['instructor'], self.lecture1.instructor)
        second_lecture_data = response_data[1]
        self.assertEqual(second_lecture_data['title'], self.lecture2.title)
        self.assertEqual(second_lecture_data['instructor'], self.lecture2.instructor)

    #
    # def test_get_lecture_list(self):
    #
    #     # Then
