import random
import copy
import logging

from .models import Instructor, Room, MeetingTime, Department, Course, Section, Class

logger = logging.getLogger(__name__)


class GeneticAlgorithm:
    def __init__(self, department_ids, years, semester, population_size=50,
                 mutation_rate=0.1, elite_rate=0.1, generations=500):
        self.department_ids = department_ids if isinstance(department_ids, list) else [department_ids]
        self.years = years if isinstance(years, list) else [years]
        self.semester = semester
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.elite_rate = elite_rate
        self.generations = generations

        # Get data from database for all selected departments and years
        self.departments = Department.objects.filter(id__in=self.department_ids)
        # ensure semester attr used correctly (use self.semester)
        self.sections = Section.objects.filter(
            department__in=self.departments,
            year__in=self.years,
            semester=self.semester
        )
        self.instructors = Instructor.objects.filter(is_available=True)
        self.rooms = Room.objects.filter(is_available=True)
        # exclude lunch break slots (assumes MeetingTime.is_lunch_break set)
        self.meeting_times = MeetingTime.objects.filter(is_lunch_break=False).order_by('day', 'start_time')

        # Generate the required classes list (list of dicts) used by GA
        self.all_classes = self._generate_required_classes()

    def _generate_required_classes(self):
        """
        Generate all required class slots for selected sections.
        Works when Course model has a ManyToMany -> sections or if Section has courses (it handles both).
        """
        classes = []

        logger.info("GA DEBUG: Selected departments: %s", [d.name for d in self.departments])
        logger.info("GA DEBUG: Sections count: %d", self.sections.count())

        total_before = 0

        for section in self.sections:
            # Try several ways to find courses for this section:
            # 1) If Course has a 'sections' M2M (most recent model): Course.objects.filter(sections=section)
            # 2) If Section has 'courses' M2M: section.courses.all()
            # We'll prefer Course.objects.filter(sections=section) to be robust.
            try:
                candidate_courses = Course.objects.filter(sections=section)
            except Exception:
                candidate_courses = section.courses.all() if hasattr(section, 'courses') else Course.objects.none()

            # If Course has year attribute, prefer courses matching the section.year
            filtered_courses = []
            for course in candidate_courses:
                # If course has 'year' attribute, require it to match the section's year
                if hasattr(course, 'year'):
                    if course.year == section.year:
                        filtered_courses.append(course)
                else:
                    filtered_courses.append(course)

            logger.info("GA DEBUG: Section %s -> courses loaded: %d", section.section_id, len(filtered_courses))

            for course in filtered_courses:
                # classes_per_week indicates how many slots this course needs for that section
                num_slots = getattr(course, 'classes_per_week', 1) or 1
                for i in range(num_slots):
                    class_obj = {
                        'id': f"{section.section_id}_{course.course_id}_{i}",
                        'course': course,
                        'section': section,
                        'duration': getattr(course, 'duration', 1),
                        'instructor': None,
                        'room': None,
                        'meeting_time': None,
                        'consecutive_slots': []
                    }
                    classes.append(class_obj)

            total_after = len(classes)
            logger.info("GA DEBUG: Total generated classes so far: %d", total_after)
            total_before = total_after

        logger.info("GA DEBUG: Total generated class slots: %d", len(classes))
        return classes

    def generate_initial_population(self):
        """Generate initial population of timetables"""
        population = []

        for _ in range(self.population_size):
            individual = copy.deepcopy(self.all_classes)

            # Assign random instructor, room, and time to each class
            for class_obj in individual:
                # Assign instructor from course instructors, fallback to any available
                try:
                    available_instructors = list(class_obj['course'].instructors.all())
                except Exception:
                    available_instructors = []

                if available_instructors:
                    class_obj['instructor'] = random.choice(available_instructors)
                elif self.instructors:
                    class_obj['instructor'] = random.choice(list(self.instructors))
                else:
                    class_obj['instructor'] = None

                # Assign room based on course requirements, fallback to any available
                suitable_rooms = self._get_suitable_rooms(class_obj['course'])
                if suitable_rooms:
                    class_obj['room'] = random.choice(suitable_rooms)
                elif self.rooms:
                    class_obj['room'] = random.choice(list(self.rooms))
                else:
                    class_obj['room'] = None

                # Assign meeting time
                if class_obj['duration'] == 2:
                    # For lab sessions, find consecutive slots
                    consecutive_slots = self._find_consecutive_slots()
                    if consecutive_slots:
                        slots = random.choice(consecutive_slots)
                        class_obj['meeting_time'] = slots[0]
                        class_obj['consecutive_slots'] = slots
                    else:
                        class_obj['meeting_time'] = None
                        class_obj['consecutive_slots'] = []
                else:
                    if self.meeting_times:
                        class_obj['meeting_time'] = random.choice(list(self.meeting_times))
                    else:
                        class_obj['meeting_time'] = None

            population.append(individual)

        return population

    def _get_suitable_rooms(self, course):
        """Get rooms suitable for the course"""
        try:
            course_type = getattr(course, 'course_type', '').lower()
        except Exception:
            course_type = ''

        if course_type == 'lab':
            return list(self.rooms.filter(room_type='Lab'))
        else:
            return list(self.rooms.filter(capacity__gte=getattr(course, 'max_students', 0)))

    def _find_consecutive_slots(self):
        """Find consecutive time slots for lab sessions"""
        consecutive_slots = []
        times_by_day = {}

        # Group meeting times by day
        for mt in self.meeting_times:
            times_by_day.setdefault(mt.day, []).append(mt)

        # Find consecutive slots within each day
        for day, times in times_by_day.items():
            times_sorted = sorted(times, key=lambda x: x.start_time)
            for i in range(len(times_sorted) - 1):
                t1 = times_sorted[i]
                t2 = times_sorted[i + 1]
                # exact equality check of end == next.start for consecutive slots
                if t1.end_time == t2.start_time:
                    # Ensure not spanning lunch (if lunch marked properly)
                    if not (t1.is_lunch_break or t2.is_lunch_break):
                        consecutive_slots.append([t1, t2])

        return consecutive_slots

    def calculate_fitness(self, individual):
        """Calculate fitness score for an individual timetable"""
        conflicts = 0
        unassigned_penalty = 0
        total_classes = len(individual)

        if total_classes == 0:
            return 0  # No classes, no fitness

        # Count unassigned classes
        for class_obj in individual:
            if not class_obj.get('instructor') or not class_obj.get('room') or not class_obj.get('meeting_time'):
                unassigned_penalty += 1

        # Check conflicts only between fully assigned classes
        fully_assigned_classes = [cls for cls in individual if all([cls.get('instructor'), cls.get('room'), cls.get('meeting_time')])]
        num_fully_assigned = len(fully_assigned_classes)

        for i in range(num_fully_assigned):
            for j in range(i + 1, num_fully_assigned):
                class1 = fully_assigned_classes[i]
                class2 = fully_assigned_classes[j]

                # Check for conflicts
                if self._has_conflict(class1, class2):
                    conflicts += 1

        # Total penalties: conflicts + unassigned classes (unassigned heavily penalized)
        total_penalties = conflicts + (unassigned_penalty * 10)

        max_possible_penalties = total_classes * (total_classes - 1) / 2 + total_classes
        if max_possible_penalties == 0:
            return 100.0 if total_penalties == 0 else 0.0

        fitness = max(0, (1 - (total_penalties / max_possible_penalties)) * 100)
        return fitness

    def _has_conflict(self, class1, class2):
        """Check if two classes have any conflicts"""
        # If either has no meeting_time, can't compare (should be treated as conflict elsewhere)
        if not class1.get('meeting_time') or not class2.get('meeting_time'):
            return False

        # Time overlap conflicts
        if self._same_time_slot(class1, class2):
            # Instructor conflict
            if class1.get('instructor') and class2.get('instructor') and class1['instructor'].id == class2['instructor'].id:
                return True

            # Room conflict
            if class1.get('room') and class2.get('room') and class1['room'].id == class2['room'].id:
                return True

            # Section conflict (students can't be in two places at once)
            if class1.get('section') and class2.get('section') and class1['section'].id == class2['section'].id:
                return True

        return False

    def _get_class_time_range(self, class_obj):
        """Get the time range for a class (start_time, end_time)"""
        if class_obj.get('duration') == 2 and class_obj.get('consecutive_slots'):
            slots = class_obj['consecutive_slots']
            start_time = min(slot.start_time for slot in slots)
            end_time = max(slot.end_time for slot in slots)
            return start_time, end_time
        else:
            mt = class_obj.get('meeting_time')
            return (mt.start_time, mt.end_time) if mt else (None, None)

    def _same_time_slot(self, class1, class2):
        """Check if two classes overlap in time"""
        mt1 = class1.get('meeting_time')
        mt2 = class2.get('meeting_time')
        if not mt1 or not mt2:
            return False

        # Must be on the same day
        if mt1.day != mt2.day:
            return False

        start1, end1 = self._get_class_time_range(class1)
        start2, end2 = self._get_class_time_range(class2)
        if not start1 or not start2 or not end1 or not end2:
            return False

        # Overlap if max(start) < min(end)
        return max(start1, start2) < min(end1, end2)

    def selection(self, population, fitness_scores):
        """Tournament selection"""
        selected = []
        tournament_size = 5

        for _ in range(len(population)):
            tournament_indices = random.sample(range(len(population)), min(tournament_size, len(population)))
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]
            winner_index = tournament_indices[tournament_fitness.index(max(tournament_fitness))]
            selected.append(copy.deepcopy(population[winner_index]))

        return selected

    def crossover(self, parent1, parent2):
        """Single point crossover"""
        if len(parent1) != len(parent2):
            return parent1, parent2

        if len(parent1) < 2:
            return parent1, parent2

        crossover_point = random.randint(1, len(parent1) - 1)
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        return child1, child2

    def mutate(self, individual):
        """Mutate an individual by changing random assignments"""
        if random.random() < self.mutation_rate and individual:
            class_to_mutate = random.choice(individual)
            mutation_type = random.choice(['instructor', 'room', 'time'])

            if mutation_type == 'instructor':
                available_instructors = list(class_to_mutate['course'].instructors.all())
                if available_instructors:
                    class_to_mutate['instructor'] = random.choice(available_instructors)
                elif self.instructors:
                    class_to_mutate['instructor'] = random.choice(list(self.instructors))

            elif mutation_type == 'room':
                suitable_rooms = self._get_suitable_rooms(class_to_mutate['course'])
                if suitable_rooms:
                    class_to_mutate['room'] = random.choice(suitable_rooms)
                elif self.rooms:
                    class_to_mutate['room'] = random.choice(list(self.rooms))

            elif mutation_type == 'time':
                if class_to_mutate.get('duration') == 2:
                    consecutive_slots = self._find_consecutive_slots()
                    if consecutive_slots:
                        slots = random.choice(consecutive_slots)
                        class_to_mutate['meeting_time'] = slots[0]
                        class_to_mutate['consecutive_slots'] = slots
                else:
                    if self.meeting_times:
                        class_to_mutate['meeting_time'] = random.choice(list(self.meeting_times))

        return individual

    def evolve(self):
        """Main evolution algorithm"""
        population = self.generate_initial_population()
        best_fitness = 0
        best_individual = None
        generations_without_improvement = 0
        max_generations_without_improvement = 200

        for generation in range(self.generations):
            fitness_scores = [self.calculate_fitness(individual) for individual in population]
            current_best_fitness = max(fitness_scores)
            current_best_individual = population[fitness_scores.index(current_best_fitness)]

            if current_best_fitness > best_fitness:
                best_fitness = current_best_fitness
                best_individual = copy.deepcopy(current_best_individual)
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1

            if generations_without_improvement >= max_generations_without_improvement:
                logger.info("GA stopping early due to no improvement for %d generations", max_generations_without_improvement)
                break

            is_fully_assigned = all(
                class_obj.get('instructor') and class_obj.get('room') and class_obj.get('meeting_time')
                for class_obj in best_individual
            ) if best_individual else False

            if best_fitness >= 90.0 and is_fully_assigned:
                logger.info("GA found high-quality fully assigned solution (fitness=%.2f), stopping early", best_fitness)
                break

            selected_population = self.selection(population, fitness_scores)
            new_population = []

            elite_size = max(1, int(len(population) * self.elite_rate))
            elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)[:elite_size]
            for i in elite_indices:
                new_population.append(copy.deepcopy(population[i]))

            while len(new_population) < len(population):
                parent1 = random.choice(selected_population)
                parent2 = random.choice(selected_population)
                child1, child2 = self.crossover(parent1, parent2)
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)
                new_population.extend([child1, child2])

            population = new_population[:len(population)]

        return best_individual, best_fitness
