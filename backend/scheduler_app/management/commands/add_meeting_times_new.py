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
        # Updated to match MeetingTime.generate_default_slots() with proper post-lunch slots
        meeting_times_data = [
            # Monday
            ('MT01', 'Monday', datetime.time(9, 0), datetime.time(10, 0), False),
            ('MT02', 'Monday', datetime.time(10, 0), datetime.time(11, 0), False),
            ('MT03', 'Monday', datetime.time(11, 0), datetime.time(12, 0), False),
            ('MT04', 'Monday', datetime.time(12, 0), datetime.time(13, 0), False),
            ('MT05', 'Monday', datetime.time(13, 0), datetime.time(13, 45), True), # lunch break
            ('MT06', 'Monday', datetime.time(13, 45), datetime.time(14, 45), False), # post-lunch
            ('MT07', 'Monday', datetime.time(14, 45), datetime.time(15, 45), False), # post-lunch
            ('MT08', 'Monday', datetime.time(15, 45), datetime.time(16, 45), False), # post-lunch

            # Tuesday
            ('MT12', 'Tuesday', datetime.time(9, 0), datetime.time(10, 0), False),
            ('MT13', 'Tuesday', datetime.time(10, 0), datetime.time(11, 0), False),
            ('MT14', 'Tuesday', datetime.time(11, 0), datetime.time(12, 0), False),
            ('MT15', 'Tuesday', datetime.time(12, 0), datetime.time(13, 0), False),
            ('MT16', 'Tuesday', datetime.time(13, 0), datetime.time(13, 45), True), # lunch break
            ('MT17', 'Tuesday', datetime.time(13, 45), datetime.time(14, 45), False), # post-lunch
            ('MT18', 'Tuesday', datetime.time(14, 45), datetime.time(15, 45), False), # post-lunch
            ('MT19', 'Tuesday', datetime.time(15, 45), datetime.time(16, 45), False), # post-lunch

            # Wednesday
            ('MT23', 'Wednesday', datetime.time(9, 0), datetime.time(10, 0), False),
            ('MT24', 'Wednesday', datetime.time(10, 0), datetime.time(11, 0), False),
            ('MT25', 'Wednesday', datetime.time(11, 0), datetime.time(12, 0), False),
            ('MT26', 'Wednesday', datetime.time(12, 0), datetime.time(13, 0), False),
            ('MT27', 'Wednesday', datetime.time(13, 0), datetime.time(13, 45), True), # lunch break
            ('MT28', 'Wednesday', datetime.time(13, 45), datetime.time(14, 45), False), # post-lunch
            ('MT29', 'Wednesday', datetime.time(14, 45), datetime.time(15, 45), False), # post-lunch
            ('MT30', 'Wednesday', datetime.time(15, 45), datetime.time(16, 45), False), # post-lunch

            # Thursday
            ('MT34', 'Thursday', datetime.time(9, 0), datetime.time(10, 0), False),
            ('MT35', 'Thursday', datetime.time(10, 0), datetime.time(11, 0), False),
            ('MT36', 'Thursday', datetime.time(11, 0), datetime.time(12, 0), False),
            ('MT37', 'Thursday', datetime.time(12, 0), datetime.time(13, 0), False),
            ('MT38', 'Thursday', datetime.time(13, 0), datetime.time(13, 45), True), # lunch break
            ('MT39', 'Thursday', datetime.time(13, 45), datetime.time(14, 45), False), # post-lunch
            ('MT40', 'Thursday', datetime.time(14, 45), datetime.time(15, 45), False), # post-lunch
            ('MT41', 'Thursday', datetime.time(15, 45), datetime.time(16, 45), False), # post-lunch

            # Friday
            ('MT45', 'Friday', datetime.time(9, 0), datetime.time(10, 0), False),
            ('MT46', 'Friday', datetime.time(10, 0), datetime.time(11, 0), False),
            ('MT47', 'Friday', datetime.time(11, 0), datetime.time(12, 0), False),
            ('MT48', 'Friday', datetime.time(12, 0), datetime.time(13, 0), False),
            ('MT49', 'Friday', datetime.time(13, 0), datetime.time(13, 45), True), # lunch break
            ('MT50', 'Friday', datetime.time(13, 45), datetime.time(14, 45), False), # post-lunch
            ('MT51', 'Friday', datetime.time(14, 45), datetime.time(15, 45), False), # post-lunch
            ('MT52', 'Friday', datetime.time(15, 45), datetime.time(16, 45), False), # post-lunch
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
