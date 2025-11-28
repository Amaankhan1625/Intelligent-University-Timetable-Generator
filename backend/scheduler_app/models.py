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
DAYS_CHOICES = [
    ('Monday','Monday'), ('Tuesday','Tuesday'), ('Wednesday','Wednesday'),
    ('Thursday','Thursday'), ('Friday','Friday'), ('Saturday','Saturday')
]

class MeetingTime(models.Model):
    pid = models.CharField(max_length=10, unique=True)
    day = models.CharField(max_length=10, choices=DAYS_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_lunch_break = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.day} {self.start_time}-{self.end_time}"


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
