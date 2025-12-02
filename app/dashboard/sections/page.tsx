'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useForm, useWatch } from 'react-hook-form'
import toast from 'react-hot-toast'
import Modal from '@/components/Modal'
import { PlusIcon, PencilIcon, TrashIcon, UsersIcon } from '@heroicons/react/24/outline'

interface Section {
  id?: number
  section_id: string
  department: number
  year: number
  semester: number
  num_students: number
  instructors?: number[]
  courses?: number[]
  department_name?: string
  instructor_names?: string[]
  course_names?: string[]
  courses_detail?: CourseDetail[]
}

interface CourseDetail {
  id: number
  course_id: string
  course_name: string
  instructors: Instructor[]
}

interface Instructor {
  id: number
  name: string
  instructor_id: string
}

const years = [
  { value: 1, label: '1st Year' },
  { value: 2, label: '2nd Year' },
  { value: 3, label: '3rd Year' },
  { value: 4, label: '4th Year' },
]

const semesters = [
  { value: 1, label: 'Semester 1' },
  { value: 2, label: 'Semester 2' },
]

export default function SectionsPage() {
  const [sections, setSections] = useState<Section[]>([])
  const [departments, setDepartments] = useState<any[]>([])
  const [courses, setCourses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSection, setEditingSection] = useState<Section | null>(null)
  const [currentSemesters, setCurrentSemesters] = useState(semesters)
  const [courseInstructorAssignments, setCourseInstructorAssignments] = useState<{ [courseId: number]: number }>({})
  const [availableInstructors, setAvailableInstructors] = useState<any[]>([])

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<Section>()

  const watchedYear = watch('year')
  const watchedCourses = watch('courses')
  const watchedDepartment = watch('department')

  useEffect(() => {
    fetchSections()
    fetchDepartments()
    fetchCourses()
    fetchAvailableInstructors()
  }, [])

  const fetchAvailableInstructors = async () => {
    try {
      const res = await api.get('/instructors/')
      const data = res.data.results || res.data
      // Sort by instructor_id in ascending order
      const sortedData = data.sort((a: any, b: any) => a.instructor_id.localeCompare(b.instructor_id))
      setAvailableInstructors(sortedData)
    } catch (err) {
      console.error('❌ Error fetching instructors:', err)
    }
  }

  useEffect(() => {
    if (watchedYear) {
      const year = Number(watchedYear)
      let newSemesters = []
      if (year === 1) {
        newSemesters = [
          { value: 1, label: 'Semester 1' },
          { value: 2, label: 'Semester 2' },
        ]
      } else if (year === 2) {
        newSemesters = [
          { value: 3, label: 'Semester 3' },
          { value: 4, label: 'Semester 4' },
        ]
      } else if (year === 3) {
        newSemesters = [
          { value: 5, label: 'Semester 5' },
          { value: 6, label: 'Semester 6' },
        ]
      } else if (year === 4) {
        newSemesters = [
          { value: 7, label: 'Semester 7' },
          { value: 8, label: 'Semester 8' },
        ]
      }
      setCurrentSemesters(newSemesters)
      // Reset semester if it's not valid for the new year
      if (newSemesters.length > 0 && !newSemesters.some(sem => sem.value === Number(watch('semester')))) {
        setValue('semester', newSemesters[0].value)
      }
    }
  }, [watchedYear, setValue, watch])



  const fetchSections = async () => {
    try {
      const res = await api.get('/sections/')
      // Handle both paginated and non-paginated formats
      const data = Array.isArray(res.data)
        ? res.data
        : res.data.results || []
      setSections(data)
    } catch (err) {
      console.error('❌ Error fetching sections:', err)
      toast.error('Failed to fetch sections')
      setSections([])
    } finally {
      setLoading(false)
    }
  }

  const fetchDepartments = async () => {
    try {
      const res = await api.get('/departments/')
      setDepartments(res.data.results || res.data)
    } catch (err) {
      console.error('❌ Error fetching departments:', err)
    }
  }

  const fetchCourses = async () => {
    try {
      const res = await api.get('/courses/')
      setCourses(res.data.results || res.data)
    } catch (err) {
      console.error('❌ Error fetching courses:', err)
    }
  }

  const onSubmit = async (data: Section) => {
    try {
      const submitData = {
        ...data,
        course_instructor_assignments: courseInstructorAssignments
      }

      if (editingSection) {
        await api.put(`/sections/${editingSection.id}/`, submitData)
        toast.success('Section updated successfully')
      } else {
        await api.post('/sections/', submitData)
        toast.success('Section created successfully')
      }

      fetchSections()
      closeModal()
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Operation failed')
    }
  }

  const deleteSection = async (id: number) => {
    if (!confirm('Are you sure you want to delete this section?')) return

    try {
      await api.delete(`/sections/${id}/`)
      toast.success('Section deleted successfully')
      fetchSections()
    } catch (error) {
      toast.error('Failed to delete section')
    }
  }

  const openModal = async (section?: Section) => {
    if (section) {
      setEditingSection(section)
      Object.keys(section).forEach((key) => {
        setValue(key as keyof Section, section[key as keyof Section])
      })
      // Load existing course instructor assignments from section.courses_detail
      const assignments: { [courseId: number]: number } = {}
      if (section.courses_detail) {
        section.courses_detail.forEach(courseDetail => {
          // Take the first instructor as single selection
          if (courseDetail.instructors.length > 0) {
            assignments[courseDetail.id] = courseDetail.instructors[0].id
          }
        })
      }
      setCourseInstructorAssignments(assignments)
    } else {
      setEditingSection(null)
      reset({ year: 1, semester: 1, num_students: 60, instructors: [], courses: [] })
      setCourseInstructorAssignments({})
    }
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingSection(null)
    reset()
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="h-8 bg-gray-200 rounded w-48 animate-pulse"></div>
          <div className="h-10 bg-gray-200 rounded w-32 animate-pulse"></div>
        </div>
        <div className="card p-6">
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded animate-pulse"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sections</h1>
          <p className="text-gray-600">Manage student sections and groups</p>
        </div>
        <button
          onClick={() => openModal()}
          className="btn-primary flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Add Section
        </button>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="table-header">
                <th className="px-6 py-3 text-left">Section ID</th>
                <th className="px-6 py-3 text-left">Department</th>
                <th className="px-6 py-3 text-left">Year</th>
                <th className="px-6 py-3 text-left">Semester</th>
                <th className="px-6 py-3 text-left">Students</th>
                <th className="px-6 py-3 text-left">Instructors</th>
                <th className="px-6 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sections.map((section) => (
                <tr key={section.id} className="hover:bg-gray-50">
                  <td className="table-cell font-mono">{section.section_id}</td>
                  <td className="table-cell">{section.department_name || 'N/A'}</td>
                  <td className="table-cell">{section.year} Year</td>
                  <td className="table-cell">Semester {section.semester}</td>
                  <td className="table-cell">{section.num_students} students</td>
                  <td className="table-cell">
                    {section.instructor_names && section.instructor_names.length > 0
                      ? section.instructor_names.join(', ')
                      : 'No instructors assigned'
                    }
                  </td>
                  <td className="table-cell">
                    <div className="flex gap-2">
                      <button
                        onClick={() => openModal(section)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteSection(section.id!)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {sections.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No sections found. Add your first section to get started.
            </div>
          )}
        </div>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingSection ? 'Edit Section' : 'Add New Section'}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Section ID
            </label>
            <input
              {...register('section_id', { required: 'Section ID is required' })}
              className="input-field"
              placeholder="e.g., CS-A, MECH-B"
            />
            {errors.section_id && (
              <p className="text-red-600 text-sm mt-1">{errors.section_id.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Department
            </label>
            <select
              {...register('department', { required: 'Department is required' })}
              className="input-field"
            >
              <option value="">Select Department</option>
              {departments.map(dept => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                </option>
              ))}
            </select>
            {errors.department && (
              <p className="text-red-600 text-sm mt-1">{errors.department.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Year
              </label>
              <select
                {...register('year', { required: 'Year is required' })}
                className="input-field"
              >
                {years.map(year => (
                  <option key={year.value} value={year.value}>
                    {year.label}
                  </option>
                ))}
              </select>
              {errors.year && (
                <p className="text-red-600 text-sm mt-1">{errors.year.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Semester
              </label>
              <select
                {...register('semester', { required: 'Semester is required' })}
                className="input-field"
              >
                {currentSemesters.map(sem => (
                  <option key={sem.value} value={sem.value}>
                    {sem.label}
                  </option>
                ))}
              </select>
              {errors.semester && (
                <p className="text-red-600 text-sm mt-1">{errors.semester.message}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Courses
            </label>
            <select
              {...register('courses')}
              multiple
              className="input-field"
              size={4}
            >
              {courses.map(course => (
                <option key={course.id} value={course.id}>
                  {course.course_id} - {course.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Hold Ctrl/Cmd to select multiple courses.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Number of Students
            </label>
            <input
              {...register('num_students', {
                required: 'Number of students is required',
                min: { value: 1, message: 'Must have at least 1 student' }
              })}
              type="number"
              className="input-field"
              placeholder="e.g., 60"
            />
            {errors.num_students && (
              <p className="text-red-600 text-sm mt-1">{errors.num_students.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Section Instructors
            </label>
            <select
              {...register('instructors')}
              multiple
              className="input-field"
              size={3}
            >
              {availableInstructors.map(instructor => (
                <option key={instructor.id} value={instructor.id}>
                  {instructor.name} ({instructor.instructor_id})
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Hold Ctrl/Cmd to select multiple instructors for this section.
            </p>
          </div>

          {watchedCourses && watchedCourses.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Course Instructor Assignments
              </label>
              <div className="space-y-4">
                {watchedCourses.map((courseId: number) => {
                  const course = courses.find(c => c.id === courseId)
                  if (!course) return null

                  return (
                    <div key={courseId} className="border rounded-lg p-4 bg-gray-50">
                      <h4 className="font-medium text-gray-900 mb-2">
                        {course.course_id} - {course.course_name}
                      </h4>
                      <select
                        className="input-field"
                        value={courseInstructorAssignments[courseId] || ''}
                        onChange={(e) => {
                          const selectedInstructor = Number(e.target.value)
                          setCourseInstructorAssignments(prev => ({
                            ...prev,
                            [courseId]: selectedInstructor
                          }))
                        }}
                      >
                        <option value="">Select Instructor</option>
                        {course.instructors.sort((a: Instructor, b: Instructor) => a.instructor_id.localeCompare(b.instructor_id)).map(instructor => (
                          <option key={instructor.id} value={instructor.id}>
                            {instructor.name} ({instructor.instructor_id})
                          </option>
                        ))}
                      </select>
                      <p className="text-xs text-gray-500 mt-1">
                        Select one instructor for this course.
                      </p>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button type="submit" className="btn-primary flex-1">
              {editingSection ? 'Update' : 'Create'} Section
            </button>
            <button
              type="button"
              onClick={closeModal}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

