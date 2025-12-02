import random
import copy
import logging
import datetime

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

        logger.info("GA Initializing with: department_ids=%s, years=%s, semester=%s", department_ids, years, semester)

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
        # exclude lunch break slots and Saturday to focus on weekday scheduling
        # Note: meeting_times will be filtered per course based on duration in generate_initial_population
        self.all_meeting_times = MeetingTime.objects.filter(
            is_lunch_break=False,
            day__in=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        ).order_by('day', 'start_time')
        self.meeting_times = list(self.all_meeting_times)  # For backward compatibility

        # Assign rooms to sections based on student strength
        self._assign_rooms_to_sections()

        logger.info("GA Data Loaded: %d sections, %d instructors, %d rooms, %d meeting_times",
                    self.sections.count(), self.instructors.count(), self.rooms.count(), len(self.meeting_times))

        # Generate the required classes list (list of dicts) used by GA
        self.all_classes = self._generate_required_classes()

    def _assign_rooms_to_sections(self):
        """Assign one room per section based on student strength, preferring larger rooms and lab rooms for sections with labs"""
        # Sort sections by student strength in descending order
        sorted_sections = sorted(self.sections, key=lambda s: s.num_students, reverse=True)

        # Keep track of assigned rooms
        assigned_rooms = set()

        for section in sorted_sections:
            # Check if section has any lab courses
            has_labs = section.courses.filter(course_type='Lab').exists()

            if has_labs:
                # For sections with labs, prioritize lab rooms that can accommodate students
                available_rooms = [room for room in self.rooms if room.id not in assigned_rooms and room.room_type == 'Lab' and room.capacity >= section.num_students]
                if not available_rooms:
                    # Fallback to any room if no lab rooms available
                    available_rooms = [room for room in self.rooms if room.id not in assigned_rooms and room.capacity >= section.num_students]
                available_rooms.sort(key=lambda r: r.capacity, reverse=True)
            else:
                # For non-lab sections, use any room based on capacity
                available_rooms = [room for room in self.rooms if room.id not in assigned_rooms and room.capacity >= section.num_students]
                available_rooms.sort(key=lambda r: r.capacity, reverse=True)

            if available_rooms:
                # Assign the largest available room
                assigned_room = available_rooms[0]
                section.room = assigned_room
                assigned_rooms.add(assigned_room.id)
                logger.info("Assigned room %s (capacity %d, type: %s) to section %s (students %d, has_labs: %s)",
                           assigned_room.room_number, assigned_room.capacity, assigned_room.room_type, section.section_id, section.num_students, has_labs)
            else:
                logger.warning("No suitable room found for section %s (students %d)", section.section_id, section.num_students)
                section.room = None

        # Save the section assignments to database
        for section in sorted_sections:
            section.save()

    def _generate_required_classes(self):
        """
        Generate all required class slots for selected sections.
        Gets all courses for each section's department and year, then generates classes_per_week slots for each.
        """
        classes = []

        logger.info("GA DEBUG: Selected departments: %s", [d.name for d in self.departments])
        logger.info("GA DEBUG: Sections count: %d", self.sections.count())

        for section in self.sections:
            # Get all courses for this section
            candidate_courses = section.courses.all()

            logger.info("GA DEBUG: Section %s (Dept: %s, Year: %d) -> courses loaded: %d",
                       section.section_id, section.department.name if section.department else 'None', section.year, len(candidate_courses))

            for course in candidate_courses:
                # classes_per_week indicates how many slots this course needs for that section
                num_slots = getattr(course, 'classes_per_week', 1) or 1
                logger.info("GA DEBUG: Course %s has classes_per_week: %d", course.course_name, num_slots)

                for i in range(num_slots):
                    class_obj = {
                        'id': f"{section.section_id}_{course.course_id}_{i}",
                        'course': course,
                        'section': section,
                        'duration': getattr(course, 'duration', 1),
                        'instructor': None,
                        'room': None,
                        'meeting_time': None
                    }
                    classes.append(class_obj)

        logger.info("GA DEBUG: Total generated class slots: %d", len(classes))
        return classes

    def _get_suitable_meeting_times(self, course):
        """Get meeting times suitable for the course based on its duration and type"""
        duration = getattr(course, 'duration', 1)
        course_type = getattr(course, 'course_type', '')

        # Start with all available meeting times
        base_times = list(self.all_meeting_times)

        # Exclude 12:00 slot for lab courses
        if course_type == 'Lab':
            base_times = [mt for mt in base_times if mt.start_time != datetime.time(12, 0)]

        if duration == 1:
            # All filtered meeting times are suitable for 1-hour courses
            return base_times
        else:
            # For courses longer than 1 hour, only allow slots that won't cause the class to extend beyond 17:00
            suitable_times = []
            for mt in base_times:
                # Calculate the actual end time
                start_time = mt.start_time
                end_time = datetime.time(hour=(start_time.hour + duration) % 24, minute=start_time.minute)
                # Check if the class ends by 17:00
                if end_time <= datetime.time(17, 0):
                    suitable_times.append(mt)
            return suitable_times

    def generate_initial_population(self):
        """Generate initial population of timetables"""
        population = []

        for _ in range(self.population_size):
            individual = copy.deepcopy(self.all_classes)
            used_rooms = {}  # Track used rooms per (day, start_time) to avoid conflicts

            # Assign random instructor, room, and time to each class
            for idx, class_obj in enumerate(individual):
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

                # Assign meeting time based on course duration, ensuring no conflicts with previous classes
                suitable_times = self._get_suitable_meeting_times(class_obj['course'])
                available_times = []
                for mt in suitable_times:
                    conflict = False
                    for prev_class in individual[:idx]:
                        if prev_class.get('meeting_time') and prev_class.get('instructor') == class_obj.get('instructor') and self._same_time_slot(prev_class, {'meeting_time': mt, 'duration': class_obj.get('duration', 1)}):
                            conflict = True
                            break
                        if prev_class.get('meeting_time') and prev_class.get('section') == class_obj.get('section') and self._same_time_slot(prev_class, {'meeting_time': mt, 'duration': class_obj.get('duration', 1)}):
                            conflict = True
                            break
                    if not conflict:
                        available_times.append(mt)

                if available_times:
                    class_obj['meeting_time'] = random.choice(available_times)
                elif suitable_times:
                    # Fallback to any suitable time if no conflict-free time found
                    class_obj['meeting_time'] = random.choice(suitable_times)
                else:
                    # Fallback to any meeting time if no suitable ones found
                    if self.meeting_times:
                        class_obj['meeting_time'] = random.choice(list(self.meeting_times))
                    else:
                        class_obj['meeting_time'] = None

                # Assign room from section's assigned room, fallback to course requirements, ensuring no conflict
                if class_obj['section'].room:
                    # Check if room is available at this time
                    time_key = (class_obj['meeting_time'].day, class_obj['meeting_time'].start_time) if class_obj['meeting_time'] else None
                    if time_key and time_key not in used_rooms:
                        used_rooms[time_key] = set()
                    if time_key and class_obj['section'].room.id not in used_rooms[time_key]:
                        class_obj['room'] = class_obj['section'].room
                        used_rooms[time_key].add(class_obj['section'].room.id)
                    else:
                        # Room not available, fallback
                        suitable_rooms = self._get_suitable_rooms(class_obj['course'])
                        available_rooms = [r for r in suitable_rooms if time_key and r.id not in used_rooms[time_key]]
                        if available_rooms:
                            class_obj['room'] = random.choice(available_rooms)
                            used_rooms[time_key].add(class_obj['room'].id)
                        elif self.rooms:
                            available_rooms = [r for r in list(self.rooms) if time_key and r.id not in used_rooms[time_key]]
                            if available_rooms:
                                class_obj['room'] = random.choice(available_rooms)
                                used_rooms[time_key].add(class_obj['room'].id)
                            else:
                                class_obj['room'] = None
                        else:
                            class_obj['room'] = None
                else:
                    # Fallback to course requirements if section has no room assigned
                    suitable_rooms = self._get_suitable_rooms(class_obj['course'])
                    time_key = (class_obj['meeting_time'].day, class_obj['meeting_time'].start_time) if class_obj['meeting_time'] else None
                    if time_key and time_key not in used_rooms:
                        used_rooms[time_key] = set()
                    available_rooms = [r for r in suitable_rooms if time_key and r.id not in used_rooms[time_key]]
                    if available_rooms:
                        class_obj['room'] = random.choice(available_rooms)
                        used_rooms[time_key].add(class_obj['room'].id)
                    elif self.rooms:
                        available_rooms = [r for r in list(self.rooms) if time_key and r.id not in used_rooms[time_key]]
                        if available_rooms:
                            class_obj['room'] = random.choice(available_rooms)
                            used_rooms[time_key].add(class_obj['room'].id)
                        else:
                            class_obj['room'] = None
                    else:
                        class_obj['room'] = None

            population.append(individual)

        return population

    def _get_suitable_rooms(self, course):
        """Get rooms suitable for the course"""
        try:
            course_type = getattr(course, 'course_type', '')
        except Exception:
            course_type = ''

        if course_type == 'Lab':
            return list(self.rooms.filter(room_type='Lab'))
        else:
            return list(self.rooms.filter(capacity__gte=getattr(course, 'max_students', 0)))



    def calculate_fitness(self, individual):
        """Calculate fitness score for an individual timetable"""
        conflicts = 0
        unassigned_penalty = 0
        soft_constraint_penalty = 0
        distribution_penalty = 0
        lunch_break_penalty = 0
        total_classes = len(individual)

        if total_classes == 0:
            return 0  # No classes, no fitness

        # Count unassigned classes and soft constraint violations
        for class_obj in individual:
            if not class_obj.get('instructor') or not class_obj.get('room') or not class_obj.get('meeting_time'):
                # Higher penalty for unassigned lab classes to prioritize them
                if class_obj.get('course') and class_obj['course'].course_type == 'Lab':
                    unassigned_penalty += 50  # Increased penalty for labs
                else:
                    unassigned_penalty += 40  # Increased penalty for theory classes

            # Soft constraint for labs in lab rooms
            if class_obj.get('course') and class_obj.get('room'):
                if class_obj['course'].course_type == 'Lab' and class_obj['room'].room_type != 'Lab':
                    soft_constraint_penalty += 5  # Increased penalty for labs not in lab rooms

            # Penalty for classes that span lunch break
            if self._spans_lunch_break(class_obj):
                lunch_break_penalty += 100  # High penalty for spanning lunch break

            # Penalty for any class scheduled right before lunch break (ending at 13:00) to avoid discontinuity
            if class_obj.get('meeting_time'):
                start_time, end_time = self._get_class_time_range(class_obj)
                if end_time == datetime.time(13, 0):
                    lunch_break_penalty += 100  # Moderate penalty for any class ending right before lunch

        # Check conflicts only between fully assigned classes
        fully_assigned_classes = [cls for cls in individual if all([cls.get('instructor'), cls.get('room'), cls.get('meeting_time')])]
        num_fully_assigned = len(fully_assigned_classes)

        # Add distribution penalty (only for weekdays since Saturday is excluded)
        scheduled_days = [c['meeting_time'].day for c in fully_assigned_classes if c.get('meeting_time')]
        if scheduled_days:
            days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            day_counts = [scheduled_days.count(day) for day in days_of_week]

            mean = sum(day_counts) / len(day_counts)
            variance = sum([(count - mean) ** 2 for count in day_counts]) / len(day_counts)
            std_dev = variance ** 0.5
            distribution_penalty = std_dev * 10

        # Add penalty for not using post-lunch slots (13:45 and later)
        post_lunch_times = [mt for mt in self.meeting_times if mt.start_time >= datetime.time(13, 45)]
        post_lunch_scheduled = [c for c in fully_assigned_classes if c.get('meeting_time') and c['meeting_time'] in post_lunch_times]
        if post_lunch_times and len(post_lunch_scheduled) == 0:
            # Penalty if no post-lunch slots are used at all - increased to 50 points
            post_lunch_penalty = 50
        else:
            post_lunch_penalty = 0

        # Add penalty for courses not meeting classes_per_week requirement
        classes_per_week_penalty = 0
        course_class_counts = {}
        for class_obj in fully_assigned_classes:
            course = class_obj.get('course')
            if course:
                course_id = course.id
                if course_id not in course_class_counts:
                    course_class_counts[course_id] = 0
                course_class_counts[course_id] += 1

        for course_id, actual_count in course_class_counts.items():
            try:
                course = Course.objects.get(id=course_id)
                required_count = getattr(course, 'classes_per_week', 1) or 1
                if actual_count < required_count:
                    classes_per_week_penalty += (required_count - actual_count) * 100  # Increased to 100 points per missing class for higher priority
            except Course.DoesNotExist:
                continue

        for i in range(num_fully_assigned):
            for j in range(i + 1, num_fully_assigned):
                class1 = fully_assigned_classes[i]
                class2 = fully_assigned_classes[j]

                # Check for conflicts
                if self._has_conflict(class1, class2):
                    conflicts += 1

        # Total penalties: conflicts (increased weight) + unassigned classes + post-lunch penalty + classes_per_week penalty + lunch break penalty
        total_penalties = (conflicts * 10000) + (unassigned_penalty * 50) + (soft_constraint_penalty * 10) + distribution_penalty + post_lunch_penalty + classes_per_week_penalty + lunch_break_penalty

        max_possible_penalties = (total_classes * (total_classes - 1) / 2) * 1000 + total_classes * 50 + total_classes * 10 + (total_classes * 5) + 50 + (total_classes * 100) + (total_classes * 100)
        if max_possible_penalties == 0:
            return 100.0 if total_penalties == 0 else 0.0

        fitness = max(0, (1 - (total_penalties / max_possible_penalties)) * 100)
        return fitness

    def _has_conflict(self, class1, class2):
        """Check if two classes have any conflicts"""
        # If either has no meeting_time, can't compare (should be treated as conflict elsewhere)
        if not class1.get('meeting_time') or not class2.get('meeting_time'):
            return False

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
        mt = class_obj.get('meeting_time')
        if not mt:
            return (None, None)

        start_time = mt.start_time
        duration_hours = class_obj.get('duration', 1)
        end_time = datetime.time(hour=(start_time.hour + duration_hours) % 24, minute=start_time.minute)
        return start_time, end_time

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

    def _spans_lunch_break(self, class_obj):
        """Check if a class spans across the lunch break (13:00-13:45)"""
        mt = class_obj.get('meeting_time')
        if not mt:
            return False

        start_time, end_time = self._get_class_time_range(class_obj)
        if not start_time or not end_time:
            return False

        lunch_start = datetime.time(13, 0)
        lunch_end = datetime.time(13, 45)

        # Class spans lunch if it starts before lunch ends and ends after lunch starts
        return start_time < lunch_end and end_time > lunch_start

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
        """Mutate an individual by changing random assignments for each class."""
        for class_to_mutate in individual:
            if random.random() < self.mutation_rate:
                mutation_type = random.choice(['instructor', 'time'])  # Removed 'room' since rooms are now fixed per section

                if mutation_type == 'instructor':
                    available_instructors = list(class_to_mutate['course'].instructors.all())
                    if available_instructors:
                        class_to_mutate['instructor'] = random.choice(available_instructors)
                    elif self.instructors:
                        class_to_mutate['instructor'] = random.choice(list(self.instructors))
                    # If no instructors available, leave as is (shouldn't happen in practice)

                elif mutation_type == 'time':
                    suitable_times = self._get_suitable_meeting_times(class_to_mutate['course'])
                    if suitable_times:
                        class_to_mutate['meeting_time'] = random.choice(suitable_times)
                    elif self.meeting_times:
                        class_to_mutate['meeting_time'] = random.choice(list(self.meeting_times))
                    # If no times available, leave as is (shouldn't happen in practice)
        return individual

    def _repair_individual(self, individual):
        """Repair an individual by assigning suitable values to any None fields"""
        for class_obj in individual:
            if not class_obj.get('instructor'):
                # Assign instructor from course instructors, fallback to any available
                available_instructors = list(class_obj['course'].instructors.all())
                if available_instructors:
                    class_obj['instructor'] = random.choice(available_instructors)
                elif self.instructors:
                    class_obj['instructor'] = random.choice(list(self.instructors))

            if not class_obj.get('room'):
                # Assign room based on course requirements, fallback to any available
                suitable_rooms = self._get_suitable_rooms(class_obj['course'])
                if suitable_rooms:
                    class_obj['room'] = random.choice(suitable_rooms)
                elif self.rooms:
                    class_obj['room'] = random.choice(list(self.rooms))

            if not class_obj.get('meeting_time'):
                # Assign meeting time based on course duration
                suitable_times = self._get_suitable_meeting_times(class_obj['course'])
                if suitable_times:
                    class_obj['meeting_time'] = random.choice(suitable_times)
                elif self.meeting_times:
                    class_obj['meeting_time'] = random.choice(list(self.meeting_times))
        return individual

    def _meets_classes_per_week(self, individual):
        """Check if the individual meets classes_per_week requirements for all courses"""
        fully_assigned_classes = [cls for cls in individual if all([cls.get('instructor'), cls.get('room'), cls.get('meeting_time')])]
        course_class_counts = {}
        for class_obj in fully_assigned_classes:
            course = class_obj.get('course')
            if course:
                course_id = course.id
                if course_id not in course_class_counts:
                    course_class_counts[course_id] = 0
                course_class_counts[course_id] += 1

        for course_id, actual_count in course_class_counts.items():
            try:
                course = Course.objects.get(id=course_id)
                required_count = getattr(course, 'classes_per_week', 1) or 1
                if actual_count < required_count:
                    return False
            except Course.DoesNotExist:
                continue
        return True

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

            current_is_fully_assigned = all(
                class_obj.get('instructor') and class_obj.get('room') and class_obj.get('meeting_time')
                for class_obj in current_best_individual
            )

            best_is_fully_assigned = all(
                class_obj.get('instructor') and class_obj.get('room') and class_obj.get('meeting_time')
                for class_obj in best_individual
            ) if best_individual else False

            # Prioritize full assignment over fitness score
            if current_best_fitness > best_fitness or (current_is_fully_assigned and not best_is_fully_assigned):
                best_fitness = current_best_fitness
                best_individual = copy.deepcopy(current_best_individual)
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1

            if generations_without_improvement >= max_generations_without_improvement:
                logger.info("GA stopping early due to no improvement for %d generations", max_generations_without_improvement)
                break

            # Only stop early if ALL classes are fully assigned AND classes_per_week requirements are met
            if current_is_fully_assigned and self._meets_classes_per_week(current_best_individual):
                logger.info("GA found fully assigned solution meeting classes_per_week (fitness=%.2f), stopping early", current_best_fitness)
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

        # Repair the best individual to ensure all classes are fully assigned
        if best_individual:
            best_individual = self._repair_individual(best_individual)

        logger.info("GA Finished: Best fitness=%.2f", best_fitness if best_fitness is not None else -1)
        if best_individual:
            logger.info("GA Best Individual: %d classes", len(best_individual))
            # Optional: Log details of the first few classes in the best individual
            for i, class_obj in enumerate(best_individual[:3]):
                logger.info("  Class %d: Course=%s, Section=%s, Instr=%s, Room=%s, Time=%s",
                            i,
                            class_obj.get('course').course_name if class_obj.get('course') else 'N/A',
                            class_obj.get('section').section_id if class_obj.get('section') else 'N/A',
                            class_obj.get('instructor').name if class_obj.get('instructor') else 'N/A',
                            class_obj.get('room').room_number if class_obj.get('room') else 'N/A',
                            str(class_obj.get('meeting_time')) if class_obj.get('meeting_time') else 'N/A'
                            )
        else:
            logger.info("GA Best Individual: None")

        return best_individual, best_fitness
