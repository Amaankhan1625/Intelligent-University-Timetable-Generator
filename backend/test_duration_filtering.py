#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))  # Add backend directory to path
django.setup()

from scheduler_app.genetic_algorithm import GeneticAlgorithm
from scheduler_app.models import Department, Course

def test_duration_filtering():
    print("Testing duration-based meeting time filtering...")

    # Get some test data
    departments = Department.objects.all()[:1]
    if not departments:
        print("No departments found")
        return

    dept = departments[0]
    years = [1, 2, 3, 4]
    semester = 1

    # Create GA instance
    ga = GeneticAlgorithm(dept.id, years, semester, population_size=10, generations=5)

    print(f"GA initialized with {len(ga.all_meeting_times)} total meeting times")

    # Test the new method
    courses = Course.objects.filter(department=dept)[:5]
    for course in courses:
        duration = getattr(course, 'duration', 1)
        suitable_times = ga._get_suitable_meeting_times(course)
        print(f"Course: {course.course_name}, Duration: {duration}, Suitable times: {len(suitable_times)}")

        if suitable_times:
            # Check that for duration > 1, end times don't exceed 17:00
            for mt in suitable_times[:3]:  # Check first 3
                end_hour = mt.start_time.hour + duration
                if end_hour > 17:
                    print(f"  ERROR: {mt} would end at {end_hour}:00, which is after 17:00")
                else:
                    print(f"  OK: {mt} ends at {end_hour}:00")

    # Test population generation
    print("\nTesting population generation...")
    population = ga.generate_initial_population()
    print(f"Generated population with {len(population)} individuals")

    if population:
        print(f"First individual has {len(population[0])} classes")
        duration_issues = 0
        for i, cls in enumerate(population[0][:5]):  # Check first 5 classes
            mt = cls.get('meeting_time')
            duration = cls.get('duration', 1)
            course_name = cls.get('course').course_name if cls.get('course') else 'Unknown'
            if mt:
                end_hour = mt.start_time.hour + duration
                if end_hour > 17:
                    print(f"  ISSUE: Class {i} ({course_name}): Duration {duration}, Start {mt.start_time}, End hour {end_hour} > 17")
                    duration_issues += 1
                else:
                    print(f"  OK: Class {i} ({course_name}): Duration {duration}, Start {mt.start_time}, End hour {end_hour}")
            else:
                print(f"  No meeting time assigned to class {i}")

        if duration_issues == 0:
            print("✓ All classes in population respect duration constraints")
        else:
            print(f"✗ {duration_issues} classes violate duration constraints")

if __name__ == '__main__':
    test_duration_filtering()
