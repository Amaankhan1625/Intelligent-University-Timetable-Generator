'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import Modal from '@/components/Modal'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'

interface Instructor {
  id?: number
  instructor_id: string
  name: string
  email: string
  is_available: boolean
}

export default function InstructorsPage() {
  const [instructors, setInstructors] = useState<Instructor[]>([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingInstructor, setEditingInstructor] = useState<Instructor | null>(null)

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<Instructor>()

  useEffect(() => {
    fetchInstructors()
  }, [])

  const fetchInstructors = async () => {
    try {
      const response = await api.get('/instructors/')
      const data = response.data.results || response.data
      // Sort by instructor_id in ascending order
      const sortedData = data.sort((a: Instructor, b: Instructor) => a.instructor_id.localeCompare(b.instructor_id))
      setInstructors(sortedData)
    } catch (error) {
      toast.error('Failed to fetch instructors')
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = async (data: Instructor) => {
    try {
      if (editingInstructor) {
        await api.put(`/instructors/${editingInstructor.id}/`, data)
        toast.success('Instructor updated successfully')
      } else {
        await api.post('/instructors/', data)
        toast.success('Instructor created successfully')
      }

      fetchInstructors()
      closeModal()
    } catch (error: any) {
      if (error.response?.data) {
        // Handle validation errors from DRF
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

  const deleteInstructor = async (id: number) => {
    if (!confirm('Are you sure you want to delete this instructor?')) return

    try {
      await api.delete(`/instructors/${id}/`)
      toast.success('Instructor deleted successfully')
      fetchInstructors()
    } catch (error) {
      toast.error('Failed to delete instructor')
    }
  }

  const openModal = (instructor?: Instructor) => {
    if (instructor) {
      setEditingInstructor(instructor)
      Object.keys(instructor).forEach((key) => {
        setValue(key as keyof Instructor, instructor[key as keyof Instructor])
      })
    } else {
      setEditingInstructor(null)
      reset()
    }
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingInstructor(null)
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
          <h1 className="text-2xl font-bold text-gray-900">Instructors</h1>
          <p className="text-gray-600">Manage teaching faculty</p>
        </div>
        <button
          onClick={() => openModal()}
          className="btn-primary flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Add Instructor
        </button>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="table-header">
                <th className="px-6 py-3 text-left">ID</th>
                <th className="px-6 py-3 text-left">Name</th>
                <th className="px-6 py-3 text-left">Email</th>

                <th className="px-6 py-3 text-left">Status</th>
                <th className="px-6 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {instructors.map((instructor) => (
                <tr key={instructor.id} className="hover:bg-gray-50">
                  <td className="table-cell font-mono">{instructor.instructor_id}</td>
                  <td className="table-cell font-medium">{instructor.name}</td>
                  <td className="table-cell text-blue-600">{instructor.email}</td>

                  <td className="table-cell">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      instructor.is_available 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {instructor.is_available ? 'Available' : 'Unavailable'}
                    </span>
                  </td>
                  <td className="table-cell">
                    <div className="flex gap-2">
                      <button
                        onClick={() => openModal(instructor)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteInstructor(instructor.id!)}
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
          
          {instructors.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No instructors found. Add your first instructor to get started.
            </div>
          )}
        </div>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingInstructor ? 'Edit Instructor' : 'Add New Instructor'}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Instructor ID
            </label>
            <input
              {...register('instructor_id', { required: 'Instructor ID is required' })}
              className="input-field"
              placeholder="e.g., INS001"
            />
            {errors.instructor_id && (
              <p className="text-red-600 text-sm mt-1">{errors.instructor_id.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Name
            </label>
            <input
              {...register('name', { required: 'Name is required' })}
              className="input-field"
              placeholder="Full name"
            />
            {errors.name && (
              <p className="text-red-600 text-sm mt-1">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              {...register('email', { 
                required: 'Email is required',
                pattern: {
                  value: /^\S+@\S+$/i,
                  message: 'Invalid email format'
                }
              })}
              type="email"
              className="input-field"
              placeholder="email@domain.com"
            />
            {errors.email && (
              <p className="text-red-600 text-sm mt-1">{errors.email.message}</p>
            )}
          </div>



          <div className="flex items-center">
            <input
              {...register('is_available')}
              type="checkbox"
              className="h-4 w-4 text-gray-600 focus:ring-gray-500 border-gray-300 rounded"
            />
            <label className="ml-2 block text-sm text-gray-900">
              Available for scheduling
            </label>
          </div>

          <div className="flex gap-3 pt-4">
            <button type="submit" className="btn-primary flex-1">
              {editingInstructor ? 'Update' : 'Create'} Instructor
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