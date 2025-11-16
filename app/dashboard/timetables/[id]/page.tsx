'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useParams } from 'next/navigation'
import toast from 'react-hot-toast'
import TimetableGrid from '@/components/TimetableGrid'
import { 
  DocumentArrowDownIcon, 
  ArrowLeftIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'

interface TimetableClass {
  course: string
  course_id: string
  instructor: string
  room: string
  section: string
  course_type: string
}

interface TimetableData {
  timetable_name: string
  fitness: number
  schedule: Record<string, Record<string, TimetableClass[]>>
}

export default function TimetableDetailPage() {
  const [timetable, setTimetable] = useState<TimetableData | null>(null)
  const [loading, setLoading] = useState(true)
  const params = useParams()

  useEffect(() => {
    if (params.id) {
      fetchTimetable()
    }
  }, [params.id])

  const fetchTimetable = async () => {
    try {
      const response = await api.get(`/timetables/${params.id}/view_schedule/`)
      setTimetable(response.data)
    } catch (error) {
      toast.error('Failed to fetch timetable details')
    } finally {
      setLoading(false)
    }
  }

  const exportPDF = async () => {
    try {
      const response = await api.get(`/timetables/${params.id}/export_pdf/`, {
        responseType: 'blob'
      })
      
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${timetable?.timetable_name || 'timetable'}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.success('PDF exported successfully')
    } catch (error) {
      toast.error('Failed to export PDF')
    }
  }

  const exportExcel = async () => {
    try {
      const response = await api.get(`/timetables/${params.id}/export_excel/`, {
        responseType: 'blob'
      })
      
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${timetable?.timetable_name || 'timetable'}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.success('Excel exported successfully')
    } catch (error) {
      toast.error('Failed to export Excel')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="h-8 bg-gray-200 rounded w-64 animate-pulse"></div>
          <div className="flex gap-2">
            <div className="h-10 bg-gray-200 rounded w-32 animate-pulse"></div>
            <div className="h-10 bg-gray-200 rounded w-32 animate-pulse"></div>
          </div>
        </div>
        <div className="card p-6">
          <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
        </div>
      </div>
    )
  }

  if (!timetable) {
    return (
      <div className="card p-12 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Timetable not found</h3>
        <p className="text-gray-600 mb-6">
          The requested timetable could not be found or may have been deleted.
        </p>
        <Link href="/dashboard/timetables" className="btn-primary">
          Back to Timetables
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard/timetables"
            className="text-gray-400 hover:text-gray-600"
          >
            <ArrowLeftIcon className="h-6 w-6" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{timetable.timetable_name}</h1>
            <div className="flex items-center gap-4 mt-1">
              <span className="text-sm text-gray-600">
                Fitness Score: {timetable.fitness?.toFixed(1)}%
              </span>
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                timetable.fitness >= 80 ? 'bg-green-100 text-green-800' :
                timetable.fitness >= 60 ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {timetable.fitness >= 80 ? 'Excellent' :
                 timetable.fitness >= 60 ? 'Good' : 'Needs Improvement'}
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={exportPDF}
            className="btn-secondary flex items-center gap-2"
          >
            <DocumentArrowDownIcon className="h-5 w-5" />
            Export PDF
          </button>
          <button
            onClick={exportExcel}
            className="btn-secondary flex items-center gap-2"
          >
            <DocumentArrowDownIcon className="h-5 w-5" />
            Export Excel
          </button>
        </div>
      </div>

      <TimetableGrid 
        schedule={timetable.schedule}
        title="Weekly Schedule"
      />

      {timetable.fitness < 80 && (
        <div className="card p-6 bg-yellow-50 border-yellow-200">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">
            Optimization Suggestions
          </h3>
          <div className="text-sm text-yellow-700 space-y-2">
            <p>• Consider adjusting the genetic algorithm parameters for better results</p>
            <p>• Check for instructor availability conflicts</p>
            <p>• Ensure adequate room capacity for all courses</p>
            <p>• Verify meeting time slots are properly configured</p>
          </div>
        </div>
      )}
    </div>
  )
}
