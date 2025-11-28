from django.core.management.base import BaseCommand
from scheduler_app.models import MeetingTime
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Add default sample meeting time data to the database'

    def handle(self, *args, **kwargs):
        # Delete all existing MeetingTime data first
        deleted_count, _ = MeetingTime.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing MeetingTime records."))

        # Sample meeting time data: pid, day, start_time, end_time, is_lunch_break
        meeting_times_data = [
           
             ('MT01', 'Monday', datetime.time(9, 0), datetime.time(10, 0), False),
            ('MT02', 'Monday', datetime.time(10, 0), datetime.time(11, 0), False),
            ('MT03', 'Monday', datetime.time(11, 0), datetime.time(12, 0), False),
            ('MT04', 'Monday', datetime.time(12, 0), datetime.time(1, 0), False), 
            ('MT05', 'Monday', datetime.time(1, 0), datetime.time(1, 45), True), # lunch break
            ('MT06', 'Monday', datetime.time(1, 45), datetime.time(2, 45), False),
            ('MT07', 'Monday', datetime.time(2, 45), datetime.time(3, 45), False),
            ('MT08', 'Monday', datetime.time(3, 45), datetime.time(4, 45), False),
            # Repeat for other days
            ('MT09', 'Tuesday', datetime.time(9, 0), datetime.time(10, 0), False),
            ('MT10', 'Tuesday', datetime.time(10, 0), datetime.time(11, 0), False),
            ('MT11', 'Tuesday', datetime.time(11, 0), datetime.time(12, 0), False),
            ('MT12', 'Tuesday', datetime.time(12, 0), datetime.time(1, 0), False), 
            ('MT13', 'Tuesday', datetime.time(1, 0), datetime.time(1, 45), True), # lunch break
            ('MT14', 'Tuesday', datetime.time(1, 45), datetime.time(2, 45), False),
            ('MT15', 'Tuesday', datetime.time(2, 45), datetime.time(3, 45), False),
            ('MT16', 'Tuesday', datetime.time(3, 45), datetime.time(4, 45), False),

            ('MT17', 'Wednesday', datetime.time(9, 0), datetime.time(10, 0), False),
            ('MT18', 'Wednesday', datetime.time(10, 0), datetime.time(11, 0), False),
            ('MT19', 'Wednesday', datetime.time(11, 0), datetime.time(12, 0), False),
            ('MT20', 'Wednesday', datetime.time(12, 0), datetime.time(1, 0), False), 
            ('MT21', 'Wednesday', datetime.time(1, 0), datetime.time(1, 45), True), # lunch break
            ('MT22', 'Wednesday', datetime.time(1, 45), datetime.time(2, 45), False),
            ('MT23', 'Wednesday', datetime.time(2, 45), datetime.time(3, 45), False),
            ('MT24', 'Wednesday', datetime.time(3, 45), datetime.time(4, 45), False),

            ('MT25', 'Thrusday', datetime.time(9, 0), datetime.time(10, 0), False),
            ('MT26', 'Thrusday', datetime.time(10, 0), datetime.time(11, 0), False),
            ('MT27', 'Thrusday', datetime.time(11, 0), datetime.time(12, 0), False),
            ('MT28', 'Thrusday', datetime.time(12, 0), datetime.time(1, 0), False), 
            ('MT29', 'Thrusday', datetime.time(1, 0), datetime.time(1, 45), True), # lunch break
            ('MT30', 'Thrusday', datetime.time(1, 45), datetime.time(2, 45), False),
            ('MT31', 'Thrusday', datetime.time(2, 45), datetime.time(3, 45), False),
            ('MT32', 'Thrusday', datetime.time(3, 45), datetime.time(4, 45), False),

            ('MT33', 'Friday', datetime.time(9, 0), datetime.time(10, 0), False),
            ('MT34', 'Friday', datetime.time(10, 0), datetime.time(11, 0), False),
            ('MT35', 'Friday', datetime.time(11, 0), datetime.time(12, 0), False),
            ('MT36', 'Friday', datetime.time(12, 0), datetime.time(1, 0), False), 
            ('MT37', 'Friday', datetime.time(1, 0), datetime.time(1, 45), True), # lunch break
            ('MT38', 'Friday', datetime.time(1, 45), datetime.time(2, 45), False),
            ('MT39', 'Friday', datetime.time(2, 45), datetime.time(3, 45), False),
            ('MT40', 'Friday', datetime.time(3, 45), datetime.time(4, 45), False),
        ]

        added_count = 0
        for pid, day, start_time, end_time, is_lunch_break in meeting_times_data:
            mt, created = MeetingTime.objects.get_or_create(
                pid=pid,
                defaults={
                    'day': day,
                    'start_time': start_time,
                    'end_time': end_time,
                    'is_lunch_break': is_lunch_break,
                    'created_at': timezone.now(),
                    'updated_at': timezone.now(),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Added MeetingTime {pid} - {day} {start_time}-{end_time}"))
                added_count += 1
            else:
                self.stdout.write(f"MeetingTime {pid} already exists, skipping.")

        self.stdout.write(self.style.SUCCESS(f"Total MeetingTimes added: {added_count}"))
