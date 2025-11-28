import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from scheduler_app.models import Course, Department

@pytest.mark.django_db
class TestCourseAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.department = Department.objects.create(name="Test Dept", code="TD")
        # Create initial courses
        Course.objects.create(
            course_id="CS101",
            course_name="Intro to CS",
            course_type="Theory",
            credits=3,
            max_students=50,
            duration=1,
            year=1,
            sections=[],
        )
        Course.objects.create(
            course_id="CS201",
            course_name="Data Structures",
            course_type="Theory",
            credits=4,
            max_students=45,
            duration=1,
            year=2,
            sections=[],
        )

    def test_list_courses(self):
        url = reverse('course-list')
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_filter_courses_by_year(self):
        url = reverse('course-list') + "?year=1"
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.json()
        if 'results' in data:
            courses = data['results']
        else:
            courses = data
        assert all(course['year'] == 1 for course in courses)

    def test_create_course_with_year(self):
        url = reverse('course-list')
        payload = {
            "course_id": "CS301",
            "course_name": "Algorithms",
            "course_type": "Theory",
            "credits": 3,
            "max_students": 60,
            "duration": 1,
            "year": 3,
            "classes_per_week": 3
        }
        response = self.client.post(url, payload, format='json')
        assert response.status_code == 201
        created_course = Course.objects.get(course_id="CS301")
        assert created_course.year == 3

    def test_update_course_year(self):
        course = Course.objects.first()
        url = reverse('course-detail', args=[course.id])
        new_year = 4
        payload = {
            "course_id": course.course_id,
            "course_name": course.course_name,
            "course_type": course.course_type,
            "credits": course.credits,
            "max_students": course.max_students,
            "duration": course.duration,
            "year": new_year,
            "classes_per_week": course.classes_per_week
        }
        response = self.client.put(url, payload, format='json')
        assert response.status_code == 200
        course.refresh_from_db()
        assert course.year == new_year

    def test_delete_course(self):
        course = Course.objects.first()
        url = reverse('course-detail', args=[course.id])
        response = self.client.delete(url)
        assert response.status_code == 204
        with pytest.raises(Course.DoesNotExist):
            Course.objects.get(id=course.id)
