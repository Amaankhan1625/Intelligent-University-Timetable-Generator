#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler.settings')
sys.path.append('.')
django.setup()

from scheduler_app.models import Class

def test_class_lookup():
    print("Testing class lookup...")

    # Check if the specific class exists
    try:
        cls = Class.objects.get(class_id='1ST YR CSE_BSL104_1_1db6')
        print(f'✅ Class found: {cls.class_id} - {cls.course.course_name}')
        print(f'   ID: {cls.id}')
        print(f'   Instructor: {cls.instructor.name}')
        print(f'   Room: {cls.room.room_number}')
        print(f'   Meeting Time: {cls.meeting_time}')
    except Class.DoesNotExist:
        print('❌ Class not found with class_id: 1ST YR CSE_BSL104_1_1db6')

    print("\nFirst 5 classes in database:")
    for cls in Class.objects.all()[:5]:
        print(f' - ID: {cls.id}, class_id: {cls.class_id}, course: {cls.course.course_name}')

if __name__ == '__main__':
    test_class_lookup()
