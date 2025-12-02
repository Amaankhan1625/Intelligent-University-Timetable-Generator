'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import Modal from '@/components/Modal'
import { PlusIcon, PencilIcon, TrashIcon, ClockIcon } from '@heroicons/react/24/outline'

interface MeetingTime {
  id?: number
  pid: string
  day: string
  start_time: string
  end_time: string
  is_lunch_break: boolean
}

const daysOfWeek = [
  { value: 'Monday', label: 'Monday' },
  { value: 'Tuesday', label: 'Tuesday' },
  { value: 'Wednesday', label: 'Wednesday' },
  { value: 'Thursday', label: 'Thursday' },
  { value: 'Friday', label: 'Friday' },
  { value: 'Saturday', label: 'Saturday' },
]

export default function MeetingTimesPage() {
  const [meetingTimes, setMeetingTimes] = useState<MeetingTime[]>([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingMeetingTime, setEditingMeetingTime] = useState<MeetingTime | null>(null)

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<MeetingTime>()

  useEffect(() => {
    fetchMeetingTimes()
  }, [])

  const fetchMeetingTimes = async () => {
    try {
      const res = await api.get('/meeting-times/')
      // Handle both paginated and non-paginated formats
      const data = Array.isArray(res.data)
        ? res.data
        : res.data.results || []
      // Sort by pid in ascending order
      const sortedData = data.sort((a: MeetingTime, b: MeetingTime) => a.pid.localeCompare(b.pid))
      setMeetingTimes(sortedData)
    } catch (err) {
      console.error('❌ Error fetching meeting times:', err)
      toast.error('Failed to fetch meeting times')
      setMeetingTimes([])
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = async (data: MeetingTime) => {
    try {
      if (editingMeetingTime) {
        await api.put(`/meeting-times/${editingMeetingTime.id}/`, data)
        toast.success('Meeting time updated successfully')
      } else {
        await api.post('/meeting-times/', data)
        toast.success('Meeting time created successfully')
      }

      fetchMeetingTimes()
      closeModal()
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Operation failed')
    }
  }

  const deleteMeetingTime = async (id: number) => {
    if (!confirm('Are you sure you want to delete this meeting time?')) return

    try {
      await api.delete(`/meeting-times/${id}/`)
      toast.success('Meeting time deleted successfully')
      fetchMeetingTimes()
    } catch (error) {
      toast.error('Failed to delete meeting time')
    }
  }

  const openModal = (meetingTime?: MeetingTime) => {
    if (meetingTime) {
      setEditingMeetingTime(meetingTime)
      Object.keys(meetingTime).forEach((key) => {
        setValue(key as keyof MeetingTime, meetingTime[key as keyof MeetingTime])
      })
    } else {
      setEditingMeetingTime(null)
      reset({ day: 'Monday', is_lunch_break: false })
    }
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingMeetingTime(null)
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
          <h1 className="text-2xl font-bold text-gray-900">Meeting Times</h1>
          <p className="text-gray-600">Manage class scheduling times</p>
        </div>
        <button
          onClick={() => openModal()}
          className="btn-primary flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Add Meeting Time
        </button>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="table-header">
                <th className="px-6 py-3 text-left">PID</th>
                <th className="px-6 py-3 text-left">Day</th>
                <th className="px-6 py-3 text-left">Start Time</th>
                <th className="px-6 py-3 text-left">End Time</th>
                <th className="px-6 py-3 text-left">Type</th>
                <th className="px-6 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {meetingTimes.map((meetingTime) => (
                <tr key={meetingTime.id} className="hover:bg-gray-50">
                  <td className="table-cell font-mono">{meetingTime.pid}</td>
                  <td className="table-cell">{meetingTime.day}</td>
                  <td className="table-cell">{meetingTime.start_time}</td>
                  <td className="table-cell">{meetingTime.end_time}</td>
                  <td className="table-cell">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      meetingTime.is_lunch_break
                        ? 'bg-orange-100 text-orange-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {meetingTime.is_lunch_break ? 'Lunch Break' : 'Class Time'}
                    </span>
                  </td>
                  <td className="table-cell">
                    <div className="flex gap-2">
                      <button
                        onClick={() => openModal(meetingTime)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteMeetingTime(meetingTime.id!)}
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

          {meetingTimes.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No meeting times found. Add your first meeting time to get started.
            </div>
          )}
        </div>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingMeetingTime ? 'Edit Meeting Time' : 'Add New Meeting Time'}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              PID
            </label>
            <input
              {...register('pid', { required: 'PID is required' })}
              className="input-field"
              placeholder="e.g., MT001"
            />
            {errors.pid && (
              <p className="text-red-600 text-sm mt-1">{errors.pid.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Day
            </label>
            <select
              {...register('day', { required: 'Day is required' })}
              className="input-field"
            >
              {daysOfWeek.map(day => (
                <option key={day.value} value={day.value}>
                  {day.label}
                </option>
              ))}
            </select>
            {errors.day && (
              <p className="text-red-600 text-sm mt-1">{errors.day.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Time
              </label>
              <input
                {...register('start_time', { required: 'Start time is required' })}
                type="time"
                className="input-field"
              />
              {errors.start_time && (
                <p className="text-red-600 text-sm mt-1">{errors.start_time.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                End Time
              </label>
              <input
                {...register('end_time', { required: 'End time is required' })}
                type="time"
                className="input-field"
              />
              {errors.end_time && (
                <p className="text-red-600 text-sm mt-1">{errors.end_time.message}</p>
              )}
            </div>
          </div>

          <div className="flex items-center">
            <input
              {...register('is_lunch_break')}
              type="checkbox"
              className="h-4 w-4 text-gray-600 focus:ring-gray-500 border-gray-300 rounded"
            />
            <label className="ml-2 block text-sm text-gray-900">
              This is a lunch break
            </label>
          </div>

          <div className="flex gap-3 pt-4">
            <button type="submit" className="btn-primary flex-1">
              {editingMeetingTime ? 'Update' : 'Create'} Meeting Time
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

