from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Instructor, Room, MeetingTime, Department, Course, Section, Class, Timetable


# -------------------------
# User Serializer
# -------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']


# -------------------------
# Instructor Serializer
# -------------------------
class InstructorSerializer(serializers.ModelSerializer):
    course_names = serializers.SerializerMethodField()
    course_ids = serializers.SerializerMethodField()

    class Meta:
        model = Instructor
        fields = ['id', 'instructor_id', 'name', 'email', 'is_available', 'course_names', 'course_ids']

    def get_course_names(self, obj):
        return [course.course_name for course in obj.courses_teaching.all()]

    def get_course_ids(self, obj):
        return [course.id for course in obj.courses_teaching.all()]


# -------------------------
# Room Serializer
# -------------------------
class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


# -------------------------
# MeetingTime Serializer
# -------------------------
class MeetingTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingTime
        fields = '__all__'


# -------------------------
# Department Serializer
# -------------------------
class DepartmentSerializer(serializers.ModelSerializer):
    head_of_department_name = serializers.CharField(source='head_of_department.name', read_only=True)

    class Meta:
        model = Department
        fields = '__all__'


# -------------------------
# Course Serializer
# -------------------------
class CourseSerializer(serializers.ModelSerializer):
    sections = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Section.objects.all(),
        required=False
    )
    instructors = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Instructor.objects.all(),
        required=False
    )
    section_names = serializers.SerializerMethodField()
    instructor_names = serializers.SerializerMethodField()
    instructors_detail = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'

    def get_section_names(self, obj):
        return [section.section_id for section in obj.sections.all()]

    def get_instructor_names(self, obj):
        return [instructor.name for instructor in obj.instructors.all()]

    def get_instructors_detail(self, obj):
        return [{
            'id': instructor.id,
            'name': instructor.name,
            'instructor_id': instructor.instructor_id
        } for instructor in obj.instructors.all()]


# -------------------------
# Section Serializer
# -------------------------
class SectionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    instructor_names = serializers.SerializerMethodField()
    course_names = serializers.SerializerMethodField()
    courses_detail = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = '__all__'

    def get_instructor_names(self, obj):
        return [instructor.name for instructor in obj.instructors.all()]

    def get_course_names(self, obj):
        return [course.course_name for course in obj.courses.all()]

    def get_courses_detail(self, obj):
        courses = obj.courses.all()
        return [{
            'id': course.id,
            'course_id': course.course_id,
            'course_name': course.course_name,
            'instructors': [{
                'id': instructor.id,
                'name': instructor.name,
                'instructor_id': instructor.instructor_id
            } for instructor in course.instructors.all()]
        } for course in courses]


# -------------------------
# Class Serializer
# -------------------------
class ClassSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    course_id = serializers.CharField(source='course.course_id', read_only=True)
    instructor_name = serializers.CharField(source='instructor.name', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    section_id = serializers.CharField(source='section.section_id', read_only=True)
    meeting_day = serializers.CharField(source='meeting_time.day', read_only=True)
    meeting_start_time = serializers.TimeField(source='meeting_time.start_time', read_only=True)
    meeting_end_time = serializers.TimeField(source='meeting_time.end_time', read_only=True)

    class Meta:
        model = Class
        fields = '__all__'


# -------------------------
# Timetable Serializer
# -------------------------
class TimetableSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    created_by_username = serializers.SerializerMethodField()
    classes_data = ClassSerializer(source='classes', many=True, read_only=True)
    total_classes = serializers.SerializerMethodField()

    class Meta:
        model = Timetable
        fields = '__all__'

    def get_created_by_username(self, obj):
        try:
            user = User.objects.get(username=obj.created_by)
            return user.username
        except User.DoesNotExist:
            return None

    def get_total_classes(self, obj):
        return obj.classes.count()


# -------------------------
# Timetable Generation Serializer
# -------------------------
class TimetableGenerationSerializer(serializers.Serializer):
    department_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False, min_length=1)
    years = serializers.ListField(child=serializers.IntegerField(min_value=1, max_value=4), allow_empty=False, min_length=1)
    semester = serializers.IntegerField(min_value=1, max_value=2)
    population_size = serializers.IntegerField(default=50, min_value=10, max_value=200)
    mutation_rate = serializers.FloatField(default=0.1, min_value=0.01, max_value=0.5)
    elite_rate = serializers.FloatField(default=0.1, min_value=0.05, max_value=0.3)
    generations = serializers.IntegerField(default=500, min_value=50, max_value=2000)


# -------------------------
# Change Password Serializer
# -------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
