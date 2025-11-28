# backend/scheduler_app/tests/test_timetable_generation.py
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User

from scheduler_app.models import (
    Department,
    Instructor,
    Room,
    MeetingTime,
    Course,
    Section,
    Timetable
)


class TimetableGenerationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

        self.department = Department.objects.create(name='Computer Science')
        self.year = 1
        self.semester = 1

        # Create instructors
        self.instructor1 = Instructor.objects.create(name='Dr. Smith')
        self.instructor2 = Instructor.objects.create(name='Dr. Jones')

        # Create rooms
        self.room1 = Room.objects.create(room_number='101', capacity=30)
        self.room2 = Room.objects.create(room_number='102', capacity=30, room_type='Lab')

        # Create meeting times
        MeetingTime.generate_default_slots()

        # Create courses
        self.course1 = Course.objects.create(
            course_id='CS101',
            course_name='Introduction to Programming',
            department=self.department,
            year=self.year,
            semester=self.semester,
            max_students=30,
            classes_per_week=2,
        )
        self.course1.instructors.add(self.instructor1)

        self.course2 = Course.objects.create(
            course_id='CS101L',
            course_name='Introduction to Programming Lab',
            department=self.department,
            year=self.year,
            semester=self.semester,
            max_students=30,
            classes_per_week=1,
            duration=2,
            course_type='Lab'
        )
        self.course2.instructors.add(self.instructor2)

        # Create section
        self.section = Section.objects.create(
            section_id='CS-A',
            department=self.department,
            year=self.year,
            semester=self.semester,
            num_students=30,
        )
        self.section.courses.add(self.course1, self.course2)

    def test_generate_timetable_api(self):
        """
        Test timetable generation via API endpoint.
        """
        url = reverse('timetable-generate')
        data = {
            'department_id': self.department.id,
            'years': [self.year],
            'semester': self.semester,
            'generations': 10, # Use a small number of generations for speed
            'population_size': 10
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        timetable_id = response.data.get('timetable_id')
        self.assertIsNotNone(timetable_id)

        timetable = Timetable.objects.get(id=timetable_id)
        self.assertGreater(timetable.classes.count(), 0, "Timetable should have generated classes.")
