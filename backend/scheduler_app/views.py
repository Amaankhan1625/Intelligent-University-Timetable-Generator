# backend/scheduler_app/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
import logging
import uuid

from .models import (
    Instructor, Room, MeetingTime, Department,
    Course, Section, Class, Timetable
)
from .serializers import *
from .genetic_algorithm import GeneticAlgorithm
from .utils import export_timetable_pdf, export_timetable_excel

logger = logging.getLogger(__name__)


# ----------------------------------------
# ✅ User Profile (JWT-based authentication)
# ----------------------------------------
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return basic user info (used after JWT login)"""
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff
        }, status=status.HTTP_200_OK)


# ----------------------------------------
# ✅ Change Password
# ----------------------------------------
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.data.get("old_password")
            if not user.check_password(old_password):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ----------------------------------------
# ✅ Scheduler App Endpoints
# ----------------------------------------
class InstructorViewSet(viewsets.ModelViewSet):
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
    permission_classes = [permissions.IsAuthenticated]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]


class MeetingTimeViewSet(viewsets.ModelViewSet):
    queryset = MeetingTime.objects.all().order_by('pid')
    serializer_class = MeetingTimeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for MeetingTime list

    @action(detail=False, methods=['post'])
    def populate_default_slots(self, request):
        """
        Populate default meeting time slots (9:00-17:00 1hr) for Mon-Sat.
        Will not duplicate existing identical slots.
        """
        try:
            MeetingTime.generate_default_slots()
            count = MeetingTime.objects.count()
            return Response({'message': 'Default meeting times generated', 'total_slots': count})
        except Exception as e:
            logger.exception("Failed to populate default meeting times")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Optionally filter by department (id) and year.
        Example: /api/courses/?department=1&year=2
        """
        queryset = Course.objects.all()
        department = self.request.query_params.get('department')
        year = self.request.query_params.get('year')
        if department:
            queryset = queryset.filter(department_id=department)
        if year:
            try:
                year_int = int(year)
                queryset = queryset.filter(year=year_int)
            except ValueError:
                # Invalid year query parameter; return empty queryset or all courses
                queryset = queryset.none()
        return queryset


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Section.objects.all()
        department = self.request.query_params.get('department')
        year = self.request.query_params.get('year')
        if department:
            queryset = queryset.filter(department_id=department)
        if year:
            queryset = queryset.filter(year=year)
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a Section. Accepts optional
        `course_instructor_assignments` dict in payload to set instructors for courses.
        """
        data = request.data.copy()
        course_instructor_assignments = data.pop('course_instructor_assignments', {})

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        section = serializer.save()

        # Update course-instructor assignments if provided
        self._update_course_instructors(course_instructor_assignments)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Update a Section; supports same `course_instructor_assignments`.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        course_instructor_assignments = data.pop('course_instructor_assignments', {})

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        section = serializer.save()

        self._update_course_instructors(course_instructor_assignments)
        return Response(serializer.data)

    def _update_course_instructors(self, course_instructor_assignments):
        """Update instructor assignments for courses"""
        for course_id, instructor_id in course_instructor_assignments.items():
            try:
                course = Course.objects.get(id=course_id)
                instructor = Instructor.objects.get(id=instructor_id)
                # Replace the instructor list with the single instructor for that course (you can change logic)
                course.instructors.set([instructor])
            except (Course.DoesNotExist, Instructor.DoesNotExist):
                continue

    @action(detail=True, methods=['get'])
    def instructors(self, request, pk=None):
        """Get instructors who teach courses assigned to this section"""
        section = self.get_object()
        instructors = Instructor.objects.filter(courses_teaching__sections=section).distinct()
        serializer = InstructorSerializer(instructors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def auto_assign_courses(self, request, pk=None):
        """
        Assign department/year/semester matching courses to this section.
        Useful to quickly populate sections with their standard course lists.
        """
        section = self.get_object()
        try:
            dept_courses = Course.objects.filter(
                department=section.department,
                year=section.year,
                semester=section.semester
            )
            section.courses.set(dept_courses)
            return Response({
                'message': 'Courses auto-assigned to section',
                'section': section.section_id,
                'assigned_count': dept_courses.count()
            })
        except Exception as e:
            logger.exception("Failed to auto-assign courses to section")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated]


class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Timetable.objects.all()
        department = self.request.query_params.get('department')
        year = self.request.query_params.get('year')
        if department:
            queryset = queryset.filter(department_id=department)
        if year:
            queryset = queryset.filter(year=year)
        return queryset

    # ----------------------------------------
    # Generate Timetable (Genetic Algorithm)
    # ----------------------------------------
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Expected POST JSON shape (examples):
        1) Single-department single-year:
           { "department_id": 1, "years": [1], "semester": 1, ... }

        2) Combined multiple depts/years:
           { "department_ids": [1,2], "years": [1,2], "semester": 1, ... }

        The GeneticAlgorithm implementation must accept the args used below.
        """
        serializer = TimetableGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        # normalize inputs to the GA interface used here
        department_ids = data.get('department_ids') or ([data['department_id']] if data.get('department_id') else [])
        years = data.get('years') or ([data['year']] if data.get('year') else [])

        if not department_ids or not years:
            return Response({'error': 'department_ids and years (or department_id/year) are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ga = GeneticAlgorithm(
                department_ids=department_ids,
                years=years,
                semester=data['semester'],
                population_size=data.get('population_size', 50),
                mutation_rate=data.get('mutation_rate', 0.1),
                elite_rate=data.get('elite_rate', 0.1),
                generations=data.get('generations', 500)
            )
            best_solution, fitness = ga.evolve()

            # Log details about generated classes for troubleshooting
            logger.info(f"Number of classes in best_solution: {len(best_solution) if best_solution else 0}")

            missing_assignments = 0
            if best_solution:
                for class_obj in best_solution:
                    keys = ('instructor', 'room', 'meeting_time', 'course', 'section')
                    if not all(k in class_obj and class_obj[k] is not None for k in keys):
                        missing_assignments += 1
                        
            logger.info(f"Classes skipped due to missing assignments: {missing_assignments}")

            # naming metadata
            departments_qs = Department.objects.filter(id__in=department_ids)
            department_names = [d.name for d in departments_qs]
            year_names = [f"Year {y}" for y in sorted(years)]
            timetable_name = f"Combined Timetable - {', '.join(department_names)} - {', '.join(year_names)} - Semester {data['semester']} - {uuid.uuid4().hex[:8]}"

            primary_department = departments_qs.first()

            with transaction.atomic():
                timetable = Timetable.objects.create(
                    name=timetable_name,
                    department=primary_department,
                    year=min(years),
                    semester=data['semester'],
                    fitness=fitness,
                    created_by=request.user.username if request.user.is_authenticated else "admin"
                )

                if best_solution:
                    for class_data in best_solution:
                        keys = ('instructor', 'room', 'meeting_time', 'course', 'section')
                        if not all(k in class_data and class_data[k] is not None for k in keys):
                            continue

                        if class_data.get('duration', 1) == 2 and class_data.get('consecutive_slots'):
                            for i, slot in enumerate(class_data['consecutive_slots']):
                                class_id = f"{class_data['id']}_slot_{i}_{uuid.uuid4().hex[:4]}"
                                class_obj = Class.objects.create(
                                    class_id=class_id,
                                    course=class_data['course'],
                                    instructor=class_data['instructor'],
                                    meeting_time=slot,
                                    room=class_data['room'],
                                    section=class_data['section']
                                )
                                timetable.classes.add(class_obj)
                        else:
                            class_id = f"{class_data['id']}_{uuid.uuid4().hex[:4]}"
                            class_obj = Class.objects.create(
                                class_id=class_id,
                                course=class_data['course'],
                                instructor=class_data['instructor'],
                                meeting_time=class_data['meeting_time'],
                                room=class_data['room'],
                                section=class_data['section']
                            )
                            timetable.classes.add(class_obj)

                if fitness >= 80:
                    timetable.is_active = True
                    timetable.save()

            return Response({
                'message': 'Combined timetable generated successfully',
                'timetable_id': timetable.id,
                'fitness': fitness,
                'total_classes': len(best_solution) if best_solution else 0,
                'departments': department_names,
                'years': sorted(years),
                'semester': data['semester']
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception("Timetable generation failed")
            return Response({'error': f'Failed to generate timetable: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ----------------------------------------
    # View Timetable Schedule
    # ----------------------------------------
    @action(detail=True, methods=['get'])
    def view_schedule(self, request, pk=None):
        timetable = self.get_object()
        classes = timetable.classes.all()

        schedule = {day: {} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']}
        for cls in classes:
            day = cls.meeting_time.day
            time_slot = f"{cls.meeting_time.start_time}-{cls.meeting_time.end_time}"
            schedule.setdefault(day, {})
            schedule[day].setdefault(time_slot, [])
            schedule[day][time_slot].append({
                'course': cls.course.course_name,
                'course_id': cls.course.course_id,
                'instructor': cls.instructor.name,
                'room': cls.room.room_number,
                'section': cls.section.section_id,
                'course_type': cls.course.course_type
            })

        return Response({
            'timetable_name': timetable.name,
            'fitness': timetable.fitness,
            'schedule': schedule
        })

    # ----------------------------------------
    # Export Functions
    # ----------------------------------------
    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        timetable = self.get_object()
        pdf_content = export_timetable_pdf(timetable)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{timetable.name}.pdf"'
        return response

    @action(detail=True, methods=['get'])
    def export_excel(self, request, pk=None):
        timetable = self.get_object()
        excel_content = export_timetable_excel(timetable)
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{timetable.name}.xlsx"'
        return response

    # ----------------------------------------
    # Activate Timetable
    # ----------------------------------------
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        timetable = self.get_object()
        Timetable.objects.filter(
            department=timetable.department,
            year=timetable.year,
            semester=timetable.semester
        ).update(is_active=False)

        timetable.is_active = True
        timetable.save()
        return Response({'message': 'Timetable activated successfully'})


# ----------------------------------------
# ✅ JWT /auth/user/ endpoint for frontend
# ----------------------------------------
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
    })
    def export_excel(self, request, pk=None):
        timetable = self.get_object()
        excel_content = export_timetable_excel(timetable)
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{timetable.name}.xlsx"'
        return response

    # ----------------------------------------
    # Activate Timetable
    # ----------------------------------------
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        timetable = self.get_object()
        Timetable.objects.filter(
            department=timetable.department,
            year=timetable.year,
            semester=timetable.semester
        ).update(is_active=False)

        timetable.is_active = True
        timetable.save()
        return Response({'message': 'Timetable activated successfully'})


# ----------------------------------------
# ✅ JWT /auth/user/ endpoint for frontend
# ----------------------------------------
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
    })
