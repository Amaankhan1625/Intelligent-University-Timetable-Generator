#!/usr/bin/env python
import os
import sys
import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))  # Add backend directory to path
import django
django.setup()

from scheduler_app.models import MeetingTime

def test_time_parsing():
    """Test the time parsing logic used in update_slot endpoint"""
    print("Testing time parsing logic...")

    # Test cases: time_slot strings that might be sent from frontend
    test_cases = [
        "09:00:00-10:00:00",  # HH:MM:SS format
        "10:00:00-11:00:00",  # HH:MM:SS format
        "13:00:00-13:45:00",  # Lunch slot with seconds
        "09:00-10:00",        # HH:MM format (fallback)
        "10:00-11:00",        # HH:MM format (fallback)
    ]

    for time_slot in test_cases:
        print(f"\nTesting time_slot: {time_slot}")
        try:
            # Parse the time slot to find the matching MeetingTime
            start_time_str, end_time_str = time_slot.split('-')
            print(f"  start_time_str: {start_time_str}")

            # Try parsing with seconds first, then fallback to minutes only
            try:
                start_time = datetime.datetime.strptime(start_time_str.strip(), '%H:%M:%S').time()
                print(f"  Parsed with %H:%M:%S: {start_time}")
            except ValueError as e1:
                print(f"  Failed %H:%M:%S: {e1}")
                # Fallback to HH:MM format
                try:
                    start_time = datetime.datetime.strptime(start_time_str.strip(), '%H:%M').time()
                    print(f"  Parsed with %H:%M: {start_time}")
                except ValueError as e2:
                    print(f"  Failed %H:%M: {e2}")
                    continue

            # Try to find matching MeetingTime in database
            try:
                meeting_time = MeetingTime.objects.get(
                    start_time=start_time
                )
                print(f"  Found MeetingTime: {meeting_time} (day: {meeting_time.day})")
            except MeetingTime.DoesNotExist:
                print(f"  No MeetingTime found for start_time: {start_time}")
            except MeetingTime.MultipleObjectsReturned:
                # Multiple days, just show count
                count = MeetingTime.objects.filter(start_time=start_time).count()
                print(f"  Found {count} MeetingTimes for start_time: {start_time}")

        except Exception as e:
            print(f"  ERROR: {str(e)}")

    print("\nTesting complete!")

if __name__ == '__main__':
    test_time_parsing()
