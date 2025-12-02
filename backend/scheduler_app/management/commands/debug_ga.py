# backend/scheduler_app/management/commands/debug_ga.py
import logging
import datetime
from django.core.management.base import BaseCommand
from scheduler_app.models import Department
from scheduler_app.genetic_algorithm import GeneticAlgorithm

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the genetic algorithm for debugging purposes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--department_ids',
            nargs='+',
            type=int,
            default=[1],
            help='List of department IDs to schedule (default: [1])'
        )
        parser.add_argument(
            '--years',
            nargs='+',
            type=int,
            default=[1],
            help='List of years to schedule (default: [1])'
        )
        parser.add_argument(
            '--semester',
            type=int,
            default=1,
            help='Semester to schedule (default: 1)'
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting GA debugging command...")

        # --- Configure Parameters ---
        department_ids = options['department_ids']
        years = options['years']
        semester = options['semester']

        self.stdout.write(f"Parameters: department_ids={department_ids}, years={years}, semester={semester}")

        # --- Run the Genetic Algorithm ---
        try:
            ga = GeneticAlgorithm(
                department_ids=department_ids,
                years=years,
                semester=semester,
                population_size=50,
                generations=100  # Keep it short for debugging
            )

            self.stdout.write(f"GA initialized. Number of classes to schedule: {len(ga.all_classes)}")

            best_solution, fitness = ga.evolve()

            self.stdout.write(self.style.SUCCESS("GA execution finished."))
            self.stdout.write(f"Best solution fitness: {fitness}")

            if best_solution:
                self.stdout.write(f"Number of classes in solution: {len(best_solution)}")

                # Print details of scheduled classes to check post-lunch usage and room assignments
                self.stdout.write("\nScheduled classes:")
                post_lunch_count = 0
                section_rooms = {}  # Track rooms assigned to sections
                for i, class_obj in enumerate(best_solution):
                    meeting_time = class_obj.get('meeting_time')
                    room = class_obj.get('room')
                    section = class_obj.get('section')
                    if meeting_time and room and section:
                        time_str = f"{meeting_time.day} {meeting_time.start_time}-{meeting_time.end_time}"
                        room_str = f"{room.room_number} (Cap: {room.capacity})"
                        section_str = section.section_id
                        self.stdout.write(f"  {i+1}. {time_str} - Room: {room_str} - Section: {section_str}")

                        # Track room assignments per section
                        if section.id not in section_rooms:
                            section_rooms[section.id] = {'section': section.section_id, 'room': room.room_number, 'capacity': room.capacity, 'classes': 0}
                        section_rooms[section.id]['classes'] += 1

                        # Check if this is a post-lunch slot (starts at or after 13:45)
                        if meeting_time.start_time >= datetime.time(13, 45):
                            post_lunch_count += 1

                self.stdout.write(f"\nPost-lunch slots used: {post_lunch_count} out of {len(best_solution)} total classes")

                # Check classes per week requirement
                self.stdout.write("\nClasses per course:")
                course_counts = {}
                for class_obj in best_solution:
                    course = class_obj.get('course')
                    if course:
                        course_name = course.course_name
                        required = getattr(course, 'classes_per_week', 1) or 1
                        if course_name not in course_counts:
                            course_counts[course_name] = {'scheduled': 0, 'required': required}
                        course_counts[course_name]['scheduled'] += 1

                for course_name, counts in course_counts.items():
                    status = "✓" if counts['scheduled'] >= counts['required'] else "✗"
                    self.stdout.write(f"  {status} {course_name}: {counts['scheduled']}/{counts['required']} classes")
            else:
                self.stdout.write("No solution was found.")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred during GA execution: {e}"))
            logger.exception("GA debugging command failed.")

        self.stdout.write("GA debugging command finished.")
