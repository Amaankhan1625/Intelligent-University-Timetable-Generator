from django.db import models
from django.utils import timezone

# -------------------------
# Instructor
# -------------------------
class Instructor(models.Model):
    instructor_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.instructor_id} - {self.name}"

# -------------------------
# Room
# -------------------------
ROOM_TYPES = [
    ('Classroom', 'Classroom'),
    ('Lab', 'Lab'),
    ('Hall', 'Hall'),
    ('Seminar', 'Seminar'),
]

class Room(models.Model):
    room_number = models.CharField(max_length=20, unique=True)
    capacity = models.IntegerField()
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='Classroom')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room_number']

    def __str__(self):
        return f"{self.room_number} (Capacity: {self.capacity})"


# -------------------------
# MeetingTime
# -------------------------
# DAYS for scheduling: Monday–Saturday
DAYS_CHOICES = [
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
]

class MeetingTime(models.Model):
    pid = models.CharField(max_length=20, unique=True)
    day = models.CharField(max_length=10, choices=DAYS_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_lunch_break = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['pid']

    def __str__(self):
        return f"{self.day} {self.start_time}-{self.end_time}"

    @classmethod
    def generate_default_slots(cls, overwrite=False):
        """
        Create default meeting time slots for Mon–Sat.
        - Standard class slots (1 hour) from 09:00 to 19:00 with lunch break.
        - Lunch slot is 13:00 - 13:45 (45 minutes) and marked is_lunch_break=True.
        - Post-lunch slots: 13:45-14:45, 14:45-15:45, etc.
        - If a slot with same day + start_time + end_time exists, it will not duplicate.
        - If overwrite=True, existing slots with exact times will be skipped but can be removed first externally.
        """
        import datetime
        created = 0

        DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

        # standard hourly slots: 09:00-10:00, 10:00-11:00, ..., 18:00-19:00
        hourly_starts = [datetime.time(hour=h, minute=0) for h in range(9, 19)]
        # lunch slot
        lunch_start = datetime.time(hour=13, minute=0)
        lunch_end = datetime.time(hour=13, minute=45)
        # post-lunch slots
        post_lunch_starts = [datetime.time(hour=13, minute=45), datetime.time(hour=14, minute=45), datetime.time(hour=15, minute=45)]

        for day in DAYS:
            # Create hourly slots but skip creating a 13:00-14:00 hour; instead we create lunch and post-lunch slots
            for start in hourly_starts:
                # determine end time for this slot
                end_hour = (start.hour + 1)
                end_time = datetime.time(hour=end_hour, minute=0)

                # If this is the 13:00 hourly slot, skip its normal creation; we'll create lunch and post-lunch separately
                if start == lunch_start:
                    continue

                # Skip duplicates
                exists = cls.objects.filter(day=day, start_time=start, end_time=end_time).exists()
                if not exists:
                    pid = f"MT-{day[:3].upper()}-{start.strftime('%H%M')}"
                    cls.objects.create(pid=pid, day=day, start_time=start, end_time=end_time, is_lunch_break=False)
                    created += 1

            # Ensure lunch slot exists (13:00 - 13:45) for weekdays only
            if day != 'Saturday':
                lunch_exists = cls.objects.filter(day=day, start_time=lunch_start, end_time=lunch_end).exists()
                if not lunch_exists:
                    pid = f"MT-{day[:3].upper()}-LUNCH"
                    cls.objects.create(pid=pid, day=day, start_time=lunch_start, end_time=lunch_end, is_lunch_break=True)
                    created += 1

                # Create post-lunch slots (13:45-14:45, 14:45-15:45, 15:45-16:45) for weekdays only
                for post_start in post_lunch_starts:
                    post_end_hour = (post_start.hour + 1)
                    post_end = datetime.time(hour=post_end_hour, minute=post_start.minute)
                    post_exists = cls.objects.filter(day=day, start_time=post_start, end_time=post_end).exists()
                    if not post_exists:
                        pid = f"MT-{day[:3].upper()}-{post_start.strftime('%H%M')}"
                        cls.objects.create(pid=pid, day=day, start_time=post_start, end_time=post_end, is_lunch_break=False)
                        created += 1

        return created


# -------------------------
# Department
# -------------------------
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    head_of_department = models.ForeignKey(
        Instructor,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='headed_departments'  # avoid reverse query clash
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


# -------------------------
# Course
# -------------------------
COURSE_TYPES = [
    ('Theory','Theory'), ('Lab','Lab'), ('Practical','Practical')
]

class Course(models.Model):
    COURSE_YEAR_CHOICES = [(1, 1), (2, 2), (3, 3), (4, 4)]
    course_id = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=100)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES, default='Theory')
    credits = models.IntegerField(default=3)
    max_students = models.IntegerField(default=60)
    duration = models.IntegerField(default=1)  # 1 hr Theory, 2 hr Lab
    year = models.IntegerField(choices=COURSE_YEAR_CHOICES, default=1)  # Added year field
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses',
        null=True,
        blank=True
    )
    sections = models.ManyToManyField(
        'Section',
        related_name='courses'
    )
    instructors = models.ManyToManyField(
        Instructor,
        blank=True,
        related_name='courses_teaching'
    )
    classes_per_week = models.IntegerField(default=3)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['course_name']

    def __str__(self):
        return f"{self.course_id} - {self.course_name}"


# -------------------------
# Section
# -------------------------
class Section(models.Model):
    section_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    year = models.IntegerField(choices=[(1,1),(2,2),(3,3),(4,4)])
    semester = models.IntegerField()
    num_students = models.IntegerField(default=60)
    room = models.ForeignKey(
        Room,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_sections'
    )
    instructors = models.ManyToManyField(
        Instructor,
        blank=True,
        related_name='sections_teaching'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['section_id']

    def __str__(self):
        return f"{self.section_id} - Year {self.year}"


# -------------------------
# Class
# -------------------------
class Class(models.Model):
    class_id = models.CharField(max_length=50, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classes')
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='classes')
    meeting_time = models.ForeignKey(MeetingTime, on_delete=models.CASCADE, related_name='classes')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='classes')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='classes')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['meeting_time']

    def __str__(self):
        return f"{self.course.course_name} - {self.section.section_id}"


# -------------------------
# Timetable
# -------------------------
class Timetable(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='timetables'
    )
    year = models.IntegerField(choices=[(1,1),(2,2),(3,3),(4,4)])
    semester = models.IntegerField()
    classes = models.ManyToManyField(Class, blank=True, related_name='timetables')
    fitness = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)
    created_by = models.CharField(max_length=100, default="admin")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.department.name} Year {self.year}"
