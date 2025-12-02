import os
import django
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler.settings')
django.setup()

from scheduler_app.models import MeetingTime

# Check all meeting times
all_times = MeetingTime.objects.filter(is_lunch_break=False, day__in=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']).order_by('day', 'start_time')
print(f'Total weekday non-lunch meeting times: {all_times.count()}')

# Check post-lunch slots specifically
post_lunch_times = [mt for mt in all_times if mt.start_time >= datetime.time(13, 45)]
print(f'Post-lunch slots (13:45+): {len(post_lunch_times)}')

# Show first 10 slots
print('\nFirst 10 weekday slots:')
for i, mt in enumerate(all_times[:10]):
    print(f'{i+1}. {mt.day} {mt.start_time}-{mt.end_time}')

# Show post-lunch slots
print('\nPost-lunch slots:')
for i, mt in enumerate(post_lunch_times[:10]):
    print(f'{i+1}. {mt.day} {mt.start_time}-{mt.end_time}')

# Check if post-lunch slots exist for each weekday
print('\nPost-lunch slots by day:')
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
for day in days:
    day_slots = [mt for mt in post_lunch_times if mt.day == day]
    print(f'{day}: {len(day_slots)} slots')
    for mt in day_slots:
        print(f'  - {mt.start_time}-{mt.end_time}')
