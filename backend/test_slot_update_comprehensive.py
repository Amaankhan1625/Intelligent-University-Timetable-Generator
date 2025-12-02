#!/usr/bin/env python
import os
import sys
import datetime
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))  # Add backend directory to path
import django
django.setup()

from scheduler_app.models import MeetingTime, Class, Timetable, Instructor, Room, Section, Course, Department
from scheduler_app.utils import check_slot_conflicts
from scheduler_app.views import ClassViewSet
from django.test import RequestFactory
from django.contrib.auth.models import User

def test_slot_update_comprehensive():
    """Comprehensive test for slot update functionality"""
    print("=== Comprehensive Slot Update Testing ===\n")

    # Test 1: Time parsing with different formats
    print("1. Testing time parsing...")
    test_cases = [
        ("09:00:00-10:00:00", "HH:MM:SS format"),
        ("10:00-11:00", "HH:MM format"),
        ("13:45:00-14:45:00", "Post-lunch slot"),
    ]

    for time_slot, description in test_cases:
        print(f"   Testing {description}: {time_slot}")
        try:
            start_time_str, end_time_str = time_slot.split('-')
            print(f"     start_time_str: {start_time_str}")

            # Try parsing with seconds first, then fallback to minutes only
            try:
                start_time = datetime.datetime.strptime(start_time_str.strip(), '%H:%M:%S').time()
                print(f"     ✓ Parsed with %H:%M:%S: {start_time}")
            except ValueError as e1:
                print(f"     Failed %H:%M:%S: {e1}")
                # Fallback to HH:MM format
                try:
                    start_time = datetime.datetime.strptime(start_time_str.strip(), '%H:%M').time()
                    print(f"     ✓ Parsed with %H:%M: {start_time}")
                except ValueError as e2:
                    print(f"     ✗ Failed %H:%M: {e2}")
                    continue

            # Check if MeetingTime exists
            try:
                meeting_time = MeetingTime.objects.get(start_time=start_time)
                print(f"     ✓ Found MeetingTime: {meeting_time.day} {meeting_time.start_time}")
            except MeetingTime.DoesNotExist:
                print(f"     ⚠ No MeetingTime found for {start_time}")
            except MeetingTime.MultipleObjectsReturned:
                count = MeetingTime.objects.filter(start_time=start_time).count()
                print(f"     ✓ Found {count} MeetingTimes for {start_time}")

        except Exception as e:
            print(f"     ✗ ERROR: {str(e)}")

    print()

    # Test 2: Check database setup
    print("2. Checking database setup...")
    try:
        total_meeting_times = MeetingTime.objects.count()
        total_classes = Class.objects.count()
        total_timetables = Timetable.objects.count()

        print(f"   MeetingTimes: {total_meeting_times}")
        print(f"   Classes: {total_classes}")
        print(f"   Timetables: {total_timetables}")

        if total_meeting_times == 0:
            print("   ⚠ No meeting times found - run populate_default_slots")
        if total_classes == 0:
            print("   ⚠ No classes found - generate a timetable first")
        if total_timetables == 0:
            print("   ⚠ No timetables found - generate a timetable first")

    except Exception as e:
        print(f"   ✗ Database check failed: {str(e)}")

    print()

    # Test 3: Test conflict checking function
    print("3. Testing conflict checking function...")

    # Get some test data
    try:
        timetable = Timetable.objects.first()
        if not timetable:
            print("   ⚠ No timetable found for testing")
        else:
            print(f"   Using timetable: {timetable.name}")

            # Get a class from the timetable
            test_class = timetable.classes.first()
            if not test_class:
                print("   ⚠ No classes in timetable")
            else:
                print(f"   Testing with class: {test_class.class_id} ({test_class.course.course_name})")

                # Test conflict checking for the same slot (should find conflict with itself if not excluded)
                conflicts = check_slot_conflicts(
                    timetable=timetable,
                    new_day=test_class.meeting_time.day,
                    new_start_time=test_class.meeting_time.start_time,
                    instructor_id=test_class.instructor_id,
                    room_id=test_class.room_id,
                    section_id=test_class.section_id,
                    exclude_class_id=None  # Don't exclude, should find conflict
                )

                print(f"   Conflicts without exclusion: {len(conflicts)}")
                for conflict in conflicts[:3]:  # Show first 3
                    print(f"     - {conflict['type']}: {conflict['course']} at {conflict['day']} {conflict['time']}")

                # Test with exclusion (should not find conflict with itself)
                conflicts_excluded = check_slot_conflicts(
                    timetable=timetable,
                    new_day=test_class.meeting_time.day,
                    new_start_time=test_class.meeting_time.start_time,
                    instructor_id=test_class.instructor_id,
                    room_id=test_class.room_id,
                    section_id=test_class.section_id,
                    exclude_class_id=test_class.class_id  # Exclude this class
                )

                print(f"   Conflicts with exclusion: {len(conflicts_excluded)}")

                # Test with different time slot
                # Find a different time slot on the same day
                other_times = MeetingTime.objects.filter(
                    day=test_class.meeting_time.day
                ).exclude(start_time=test_class.meeting_time.start_time)[:1]

                if other_times:
                    other_time = other_times[0]
                    conflicts_different_slot = check_slot_conflicts(
                        timetable=timetable,
                        new_day=other_time.day,
                        new_start_time=other_time.start_time,
                        instructor_id=test_class.instructor_id,
                        room_id=test_class.room_id,
                        section_id=test_class.section_id,
                        exclude_class_id=test_class.class_id
                    )

                    print(f"   Conflicts for different slot ({other_time.start_time}): {len(conflicts_different_slot)}")

    except Exception as e:
        print(f"   ✗ Conflict checking test failed: {str(e)}")

    print()

    # Test 4: Test API endpoint simulation
    print("4. Testing API endpoint simulation...")

    try:
        # Create a mock request
        factory = RequestFactory()

        # Get test data
        test_class = Class.objects.first()
        if not test_class:
            print("   ⚠ No classes found for API testing")
        else:
            # Test successful update (moving to same slot should work if no conflicts)
            data = {
                'class_id': test_class.class_id,
                'day': test_class.meeting_time.day,
                'time_slot': f"{test_class.meeting_time.start_time.strftime('%H:%M:%S')}-{test_class.meeting_time.end_time.strftime('%H:%M:%S')}"
            }

            print(f"   Testing update_slot with: {data}")

            # Create view instance
            view = ClassViewSet()
            request = factory.patch('/api/classes/update_slot/', data=data, content_type='application/json')

            # Add authentication
            user = User.objects.filter(is_staff=True).first()
            if user:
                request.user = user
            else:
                # Create a test user if none exists
                user = User.objects.create_user(username='testuser', password='testpass', is_staff=True)
                request.user = user

            # Call the action
            response = view.update_slot(request)
            print(f"   Response status: {response.status_code}")

            if response.status_code == 200:
                response_data = response.data
                print(f"   ✓ Success: {response_data.get('message', 'Updated successfully')}")
            elif response.status_code == 409:
                print(f"   ⚠ Conflicts detected: {len(response.data.get('conflicts', []))} conflicts")
            else:
                print(f"   ✗ Error: {response.status_code} - {response.data}")

    except Exception as e:
        print(f"   ✗ API endpoint test failed: {str(e)}")

    print()

    # Test 5: Edge cases
    print("5. Testing edge cases...")

    # Test invalid time format
    try:
        invalid_data = {
            'class_id': 'nonexistent',
            'day': 'Monday',
            'time_slot': 'invalid-time-format'
        }

        view = ClassViewSet()
        request = factory.patch('/api/classes/update_slot/', data=invalid_data, content_type='application/json')
        request.user = User.objects.filter(is_staff=True).first() or User.objects.create_user(username='testuser2', password='testpass', is_staff=True)

        response = view.update_slot(request)
        print(f"   Invalid class_id: Status {response.status_code} - Expected 404")

        # Test invalid time format
        if Class.objects.exists():
            valid_class = Class.objects.first()
            invalid_time_data = {
                'class_id': valid_class.class_id,
                'day': 'Monday',
                'time_slot': '25:00:00-26:00:00'  # Invalid time
            }

            request2 = factory.patch('/api/classes/update_slot/', data=invalid_time_data, content_type='application/json')
            request2.user = request.user
            response2 = view.update_slot(request2)
            print(f"   Invalid time format: Status {response2.status_code} - Expected 400")

    except Exception as e:
        print(f"   ✗ Edge case testing failed: {str(e)}")

    print("\n=== Testing Complete ===")

if __name__ == '__main__':
    test_slot_update_comprehensive()
