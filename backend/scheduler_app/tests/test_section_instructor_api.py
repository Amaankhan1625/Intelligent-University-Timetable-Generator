import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from scheduler_app.models import Section, Department, Instructor

@pytest.mark.django_db
class TestSectionAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.department = Department.objects.create(name="Test Dept", code="TD")
        self.section = Section.objects.create(
            section_id="S101",
            department=self.department,
            year=1,
            semester=1,
            num_students=50
        )

    def test_list_sections(self):
        url = reverse('section-list')
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert any(s['section_id'] == "S101" for s in data)

    def test_create_section(self):
        url = reverse('section-list')
        payload = {
            "section_id": "S102",
            "department": self.department.id,
            "year": 2,
            "semester": 1,
            "num_students": 40
        }
        response = self.client.post(url, payload, format='json')
        assert response.status_code == 201
        created_section = Section.objects.get(section_id="S102")
        assert created_section.year == 2

    def test_update_section(self):
        url = reverse('section-detail', args=[self.section.id])
        payload = {
            "section_id": self.section.section_id,
            "department": self.department.id,
            "year": 3,
            "semester": self.section.semester,
            "num_students": self.section.num_students
        }
        response = self.client.put(url, payload, format='json')
        assert response.status_code == 200
        self.section.refresh_from_db()
        assert self.section.year == 3

    def test_delete_section(self):
        url = reverse('section-detail', args=[self.section.id])
        response = self.client.delete(url)
        assert response.status_code == 204
        with pytest.raises(Section.DoesNotExist):
            Section.objects.get(id=self.section.id)


@pytest.mark.django_db
class TestInstructorAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.instructor = Instructor.objects.create(
            instructor_id="I101",
            name="John Doe",
            email="john.doe@example.com"
        )

    def test_list_instructors(self):
        url = reverse('instructor-list')
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert any(i['instructor_id'] == "I101" for i in data)

    def test_create_instructor(self):
        url = reverse('instructor-list')
        payload = {
            "instructor_id": "I102",
            "name": "Jane Smith",
            "email": "jane.smith@example.com"
        }
        response = self.client.post(url, payload, format='json')
        assert response.status_code == 201
        created_instructor = Instructor.objects.get(instructor_id="I102")
        assert created_instructor.name == "Jane Smith"

    def test_update_instructor(self):
        url = reverse('instructor-detail', args=[self.instructor.id])
        payload = {
            "instructor_id": self.instructor.instructor_id,
            "name": "John Updated",
            "email": self.instructor.email
        }
        response = self.client.put(url, payload, format='json')
        assert response.status_code == 200
        self.instructor.refresh_from_db()
        assert self.instructor.name == "John Updated"

    def test_delete_instructor(self):
        url = reverse('instructor-detail', args=[self.instructor.id])
        response = self.client.delete(url)
        assert response.status_code == 204
        with pytest.raises(Instructor.DoesNotExist):
            Instructor.objects.get(id=self.instructor.id)
