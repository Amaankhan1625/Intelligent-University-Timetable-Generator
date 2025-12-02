#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append(os.path.dirname(__file__))
django.setup()

from scheduler_app.models import Course, Department

def assign_departments():
    # Get the first department as default
    default_dept = Department.objects.first()
    if not default_dept:
        print('No departments found. Please create departments first.')
        return

    courses_without_dept = Course.objects.filter(department__isnull=True)
    count = courses_without_dept.count()
    if count == 0:
        print('All courses already have departments assigned.')
        return

    courses_without_dept.update(department=default_dept)
    print(f'Assigned default department "{default_dept.name}" to {count} courses.')

if __name__ == '__main__':
    assign_departments()
