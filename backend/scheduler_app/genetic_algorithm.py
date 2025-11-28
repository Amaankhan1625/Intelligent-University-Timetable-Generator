import random
import copy
from .models import Instructor, Room, MeetingTime, Department, Course, Section, Class

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
        self.sections = Section.objects.filter(
            department__in=self.departments,
            year__in=self.years,
            semester=semester
        )
        self.instructors = Instructor.objects.filter(is_available=True)
        self.rooms = Room.objects.filter(is_available=True)
        self.meeting_times = MeetingTime.objects.filter(is_lunch_break=False).order_by('day', 'start_time')

        self.all_classes = self._generate_required_classes()
        
    def _generate_required_classes(self):
        """Generate all required classes for the timetable"""
        classes = []
        for section in self.sections:
            for course in section.courses.all():
                for i in range(course.classes_per_week):
                    class_obj = {
                        'id': f"{section.section_id}_{course.course_id}_{i}",
                        'course': course,
                        'section': section,
                        'duration': course.duration,
                        'instructor': None,
                        'room': None,
                        'meeting_time': None,
                        'consecutive_slots': []
                    }
                    classes.append(class_obj)
        return classes

    def generate_initial_population(self):
        """Generate initial population of timetables"""
        population = []
        
        for _ in range(self.population_size):
            individual = copy.deepcopy(self.all_classes)
            
            # Assign random instructor, room, and time to each class
            for class_obj in individual:
                # Assign instructor from course instructors, fallback to any available
                available_instructors = list(class_obj['course'].instructors.all())
                if available_instructors:
                    class_obj['instructor'] = random.choice(available_instructors)
                elif self.instructors:
                    class_obj['instructor'] = random.choice(self.instructors)
                else:
                    class_obj['instructor'] = None

                # Assign room based on course requirements, fallback to any available
                suitable_rooms = self._get_suitable_rooms(class_obj['course'])
                if suitable_rooms:
                    class_obj['room'] = random.choice(suitable_rooms)
                elif self.rooms:
                    class_obj['room'] = random.choice(self.rooms)
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
                        class_obj['meeting_time'] = random.choice(self.meeting_times)
                    else:
                        class_obj['meeting_time'] = None
            
            population.append(individual)
        
        return population

    def _get_suitable_rooms(self, course):
        """Get rooms suitable for the course"""
        if course.course_type == 'Lab':
            return list(self.rooms.filter(room_type='Lab'))
        else:
            return list(self.rooms.filter(
                capacity__gte=course.max_students
            ))

    def _find_consecutive_slots(self):
        """Find consecutive time slots for lab sessions"""
        consecutive_slots = []
        times_by_day = {}
        
        # Group meeting times by day
        for mt in self.meeting_times:
            if mt.day not in times_by_day:
                times_by_day[mt.day] = []
            times_by_day[mt.day].append(mt)
        
        # Find consecutive slots within each day
        for day, times in times_by_day.items():
            times.sort(key=lambda x: x.start_time)
            
            for i in range(len(times) - 1):
                if times[i].end_time == times[i + 1].start_time:
                    # Check if it's not lunch break
                    if not (times[i].start_time.hour <= 13 and times[i + 1].end_time.hour >= 14):
                        consecutive_slots.append([times[i], times[i + 1]])
        
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
        
        # Total penalties: conflicts + unassigned classes
        total_penalties = conflicts + (unassigned_penalty * 10)  # Heavily penalize unassigned

        # Calculate fitness as percentage (0-100)
        # Penalize both conflicts and unassigned classes
        # The maximum possible penalties can be simplified. A class can conflict with every other class.
        # So, for N classes, max conflicts is N*(N-1)/2. Plus N unassigned penalties.
        max_possible_penalties = total_classes * (total_classes - 1) / 2 + total_classes
        
        # Avoid division by zero
        if max_possible_penalties == 0:
            return 100.0 if total_penalties == 0 else 0.0

        fitness = max(0, (1 - (total_penalties / max_possible_penalties)) * 100)
        return fitness

    def _has_conflict(self, class1, class2):
        """Check if two classes have any conflicts"""
        # Time overlap conflicts
        if self._same_time_slot(class1, class2):
            # Instructor conflict
            if class1['instructor'].id == class2['instructor'].id:
                return True

            # Room conflict
            if class1['room'].id == class2['room'].id:
                return True

            # Section conflict (students can't be in two places at once)
            if class1['section'].id == class2['section'].id:
                return True

        return False

    def _get_class_time_range(self, class_obj):
        """Get the time range for a class (start_time, end_time)"""
        if class_obj['duration'] == 2 and class_obj.get('consecutive_slots'):
            # Lab class: use the full range from first to last slot
            slots = class_obj['consecutive_slots']
            start_time = min(slot.start_time for slot in slots)
            end_time = max(slot.end_time for slot in slots)
            return start_time, end_time
        else:
            # Regular class: use meeting_time
            return class_obj['meeting_time'].start_time, class_obj['meeting_time'].end_time

    def _same_time_slot(self, class1, class2):
        """Check if two classes overlap in time"""
        # Must be on the same day
        if class1['meeting_time'].day != class2['meeting_time'].day:
            return False

        # Get time ranges
        start1, end1 = self._get_class_time_range(class1)
        start2, end2 = self._get_class_time_range(class2)

        # Check for overlap: two intervals overlap if max(start) < min(end)
        return max(start1, start2) < min(end1, end2)

    def selection(self, population, fitness_scores):
        """Tournament selection"""
        selected = []
        tournament_size = 5
        
        for _ in range(len(population)):
            tournament_indices = random.sample(range(len(population)), 
                                             min(tournament_size, len(population)))
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
            
            # Randomly choose what to mutate
            mutation_type = random.choice(['instructor', 'room', 'time'])
            
            if mutation_type == 'instructor':
                available_instructors = list(class_to_mutate['course'].instructors.all())
                if available_instructors:
                    class_to_mutate['instructor'] = random.choice(available_instructors)
                elif self.instructors:
                    class_to_mutate['instructor'] = random.choice(self.instructors)

            elif mutation_type == 'room':
                suitable_rooms = self._get_suitable_rooms(class_to_mutate['course'])
                if suitable_rooms:
                    class_to_mutate['room'] = random.choice(suitable_rooms)
                elif self.rooms:
                    class_to_mutate['room'] = random.choice(self.rooms)
            
            elif mutation_type == 'time':
                if class_to_mutate['duration'] == 2:
                    consecutive_slots = self._find_consecutive_slots()
                    if consecutive_slots:
                        slots = random.choice(consecutive_slots)
                        class_to_mutate['meeting_time'] = slots[0]
                        class_to_mutate['consecutive_slots'] = slots
                else:
                    class_to_mutate['meeting_time'] = random.choice(self.meeting_times)
        
        return individual

    def evolve(self):
        """Main evolution algorithm"""
        population = self.generate_initial_population()
        best_fitness = 0
        best_individual = None
        generations_without_improvement = 0
        # Allow more generations without improvement for more complex problems
        max_generations_without_improvement = 200
        
        for generation in range(self.generations):
            # Calculate fitness for each individual
            fitness_scores = [self.calculate_fitness(individual) for individual in population]
            
            # Track best fitness
            current_best_fitness = max(fitness_scores)
            current_best_individual = population[fitness_scores.index(current_best_fitness)]
            
            if current_best_fitness > best_fitness:
                best_fitness = current_best_fitness
                best_individual = copy.deepcopy(current_best_individual)
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            
            # Early termination if no improvement
            if generations_without_improvement >= max_generations_without_improvement:
                break
            
            # Perfect solution found - ensure it's actually a complete one
            is_fully_assigned = all(
                class_obj.get('instructor') and class_obj.get('room') and class_obj.get('meeting_time')
                for class_obj in best_individual
            ) if best_individual else False

            if best_fitness >= 90.0 and is_fully_assigned:
                break
            
            # Selection
            selected_population = self.selection(population, fitness_scores)
            
            # Create new generation
            new_population = []
            
            # Elitism - keep best individuals
            elite_size = int(len(population) * self.elite_rate)
            elite_indices = sorted(range(len(fitness_scores)), 
                                 key=lambda i: fitness_scores[i], reverse=True)[:elite_size]
            for i in elite_indices:
                new_population.append(copy.deepcopy(population[i]))
            
            # Crossover and mutation
            while len(new_population) < len(population):
                parent1 = random.choice(selected_population)
                parent2 = random.choice(selected_population)
                
                child1, child2 = self.crossover(parent1, parent2)
                
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)
                
                new_population.extend([child1, child2])
            
            # Trim to population size
            population = new_population[:len(population)]
        
        return best_individual, best_fitness