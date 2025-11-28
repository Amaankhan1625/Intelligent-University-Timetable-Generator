'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import Modal from '@/components/Modal'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'

interface Course {
  id?: number
  course_id: string
  course_name: string
  course_type: string
  credits: number
  max_students: number
  duration: number
  classes_per_week: number
  year: number
}

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCourse, setEditingCourse] = useState<Course | null>(null)

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<Course>()

  useEffect(() => {
    fetchCourses()
  }, [])

const fetchCourses = async () => {
    setLoading(true)
    try {
      let allCourses: Course[] = []
      let nextUrl = '/courses/?limit=100'
      while (nextUrl) {
        const response = await api.get(nextUrl)
        const data = response.data
        const results = data.results || data
        allCourses = allCourses.concat(results)
        nextUrl = data.next || null
      }

      // group courses by year
      const coursesByYear: Record<number, Course[]> = {}
      allCourses.forEach((course: Course) => {
        if (!coursesByYear[course.year]) {
          coursesByYear[course.year] = []
        }
        coursesByYear[course.year].push(course)
      })

      // sort each group by full course_id string then flatten the result preserving year order
      const sortedCourses = Object.keys(coursesByYear)
        .map(yearStr => parseInt(yearStr, 10))
        .sort((a, b) => a - b)
        .flatMap(year => coursesByYear[year].sort((a: Course, b: Course) => a.course_id.localeCompare(b.course_id)))

      setCourses(sortedCourses)
    } catch (error) {
      toast.error('Failed to fetch courses')
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = async (data: Course) => {
    try {
      if (editingCourse) {
        await api.put(`/courses/${editingCourse.id}/`, data)
        toast.success('Course updated successfully')
      } else {
        await api.post('/courses/', data)
        toast.success('Course created successfully')
      }

      fetchCourses()
      closeModal()
    } catch (error: any) {
      if (error.response?.data) {
        const errors = error.response.data
        if (typeof errors === 'object') {
          const errorMessages = Object.values(errors).flat().join(', ')
          toast.error(errorMessages || 'Validation failed')
        } else {
          toast.error(errors.message || errors || 'Operation failed')
        }
      } else {
        toast.error('Operation failed')
      }
    }
  }

  const deleteCourse = async (id: number) => {
    if (!confirm('Are you sure you want to delete this course?')) return

    try {
      await api.delete(`/courses/${id}/`)
      toast.success('Course deleted successfully')
      fetchCourses()
    } catch (error) {
      toast.error('Failed to delete course')
    }
  }

  const openModal = (course?: Course) => {
    if (course) {
      setEditingCourse(course)
      Object.keys(course).forEach((key) => {
        setValue(key as keyof Course, course[key as keyof Course])
      })
    } else {
      setEditingCourse(null)
      reset()
    }
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingCourse(null)
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
          <h1 className="text-2xl font-bold text-gray-900">Courses</h1>
          <p className="text-gray-600">Manage academic courses</p>
        </div>
        <button
          onClick={() => openModal()}
          className="btn-primary flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Add Course
        </button>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="table-header">
                <th className="px-6 py-3 text-left">Course ID</th>
                <th className="px-6 py-3 text-left">Name</th>
                <th className="px-6 py-3 text-left">Type</th>
                <th className="px-6 py-3 text-left">Credits</th>
                <th className="px-6 py-3 text-left">Max Students</th>
                <th className="px-6 py-3 text-left">Duration</th>
                <th className="px-6 py-3 text-left">Classes/Week</th>
                <th className="px-6 py-3 text-left">Year</th>
                <th className="px-6 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {courses.map((course) => (
                <tr key={course.id} className="hover:bg-gray-50">
                  <td className="table-cell font-mono">{course.course_id}</td>
                  <td className="table-cell font-medium">{course.course_name}</td>
                  <td className="table-cell">{course.course_type}</td>
                  <td className="table-cell">{course.credits}</td>
                  <td className="table-cell">{course.max_students}</td>
                  <td className="table-cell">{course.duration}h</td>
                  <td className="table-cell">{course.classes_per_week}</td>
                  <td className="table-cell">{course.year}</td>
                  <td className="table-cell">
                    <div className="flex gap-2">
                      <button
                        onClick={() => openModal(course)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteCourse(course.id!)}
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

          {courses.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No courses found. Add your first course to get started.
            </div>
          )}
        </div>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingCourse ? 'Edit Course' : 'Add New Course'}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Course ID
            </label>
            <input
              {...register('course_id', { required: 'Course ID is required' })}
              className="input-field"
              placeholder="e.g., CS101"
            />
            {errors.course_id && (
              <p className="text-red-600 text-sm mt-1">{errors.course_id.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Course Name
            </label>
            <input
              {...register('course_name', { required: 'Course name is required' })}
              className="input-field"
              placeholder="Full course name"
            />
            {errors.course_name && (
              <p className="text-red-600 text-sm mt-1">{errors.course_name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Course Type
            </label>
            <select
              {...register('course_type', { required: 'Course type is required' })}
              className="input-field"
            >
              <option value="">Select type</option>
              <option value="Theory">Theory</option>
              <option value="Lab">Lab</option>
              <option value="Practical">Practical</option>
            </select>
            {errors.course_type && (
              <p className="text-red-600 text-sm mt-1">{errors.course_type.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Credits
            </label>
            <input
              {...register('credits', { required: 'Credits are required', valueAsNumber: true })}
              type="number"
              className="input-field"
              placeholder="e.g., 3"
            />
            {errors.credits && (
              <p className="text-red-600 text-sm mt-1">{errors.credits.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Students
            </label>
            <input
              {...register('max_students', { required: 'Max students is required', valueAsNumber: true })}
              type="number"
              className="input-field"
              placeholder="e.g., 60"
            />
            {errors.max_students && (
              <p className="text-red-600 text-sm mt-1">{errors.max_students.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Duration (hours)
            </label>
            <input
              {...register('duration', { required: 'Duration is required', valueAsNumber: true })}
              type="number"
              className="input-field"
              placeholder="e.g., 1"
            />
            {errors.duration && (
              <p className="text-red-600 text-sm mt-1">{errors.duration.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Classes per Week
            </label>
            <input
              {...register('classes_per_week', { required: 'Classes per week is required', valueAsNumber: true })}
              type="number"
              className="input-field"
              placeholder="e.g., 3"
            />
            {errors.classes_per_week && (
              <p className="text-red-600 text-sm mt-1">{errors.classes_per_week.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Year
            </label>
            <select
              {...register('year', { required: 'Year is required', valueAsNumber: true })}
              className="input-field"
            >
              <option value="">Select year</option>
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
              <option value={4}>4</option>
            </select>
            {errors.year && (
              <p className="text-red-600 text-sm mt-1">{errors.year.message}</p>
            )}
          </div>

          <div className="flex gap-3 pt-4">
            <button type="submit" className="btn-primary flex-1">
              {editingCourse ? 'Update' : 'Create'} Course
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
