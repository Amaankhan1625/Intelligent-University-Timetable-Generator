from django.core.management import call_command
from django.test import TestCase
from backend.scheduler_app.models import MeetingTime

class AddMeetingTimesCommandTest(TestCase):

    def test_add_meeting_times_command_creates_data(self):
        # Initially database should have zero or fewer meeting times
        initial_count = MeetingTime.objects.count()

        # Call management command
        call_command('add_meeting_times')

        # After command run, there should be more meeting times
        new_count = MeetingTime.objects.count()
        self.assertGreater(new_count, initial_count, "MeetingTime objects were not created")

        # Optional: Verify one known pid exists
        self.assertTrue(MeetingTime.objects.filter(pid="MT01").exists(), "MT01 MeetingTime not found")
