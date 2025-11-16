'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useForm } from 'react-hook-form'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { 
  SparklesIcon, 
  AdjustmentsHorizontalIcon,
  InformationCircleIcon 
} from '@heroicons/react/24/outline'

interface Department {
  id: number
  name: string
  code: string
}

interface GenerateForm {
  department_ids: number[]
  years: number[]
  semester: number
  population_size: number
  mutation_rate: number
  elite_rate: number
  generations: number
}

export default function GenerateTimetablePage() {
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const router = useRouter()

  const { register, handleSubmit, formState: { errors } } = useForm<GenerateForm>({
    defaultValues: {
      population_size: 50,
      mutation_rate: 0.1,
      elite_rate: 0.1,
      generations: 500,
    }
  })

  useEffect(() => {
    fetchDepartments()
  }, [])

  const fetchDepartments = async () => {
    try {
      const response = await api.get('/departments/')
      setDepartments(response.data.results || response.data)
    } catch (error) {
      toast.error('Failed to fetch departments')
    }
  }

  const onSubmit = async (data: GenerateForm) => {
    setLoading(true)

    try {
      const response = await api.post('/timetables/generate/', data)
      const timetableId = response.data.timetable_id
      const fitness = response.data.fitness

      toast.success(
        `Timetable generated successfully (Fitness: ${fitness?.toFixed?.(1) ?? fitness}%)`
      )

      if (timetableId) {
        router.push(`/dashboard/timetables/${timetableId}`)
      } else {
        router.push('/dashboard/timetables')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to generate timetables')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div className="text-center">
        <div className="mx-auto h-16 w-16 bg-gradient-to-br from-gray-900 to-gray-700 rounded-full flex items-center justify-center mb-4">
          <SparklesIcon className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Generate Timetable</h1>
        <p className="text-gray-600">
          Create an optimized timetable using advanced genetic algorithms
        </p>
      </div>

      <div className="card p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Departments (Select multiple)
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {departments.map(dept => (
                  <label key={dept.id} className="flex items-center p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      {...register('department_ids', { required: 'At least one department is required' })}
                      type="checkbox"
                      value={dept.id}
                      className="mr-3"
                    />
                    <span className="text-sm font-medium">{dept.code} - {dept.name}</span>
                  </label>
                ))}
              </div>
              {errors.department_ids && (
                <p className="text-red-600 text-sm mt-1">{errors.department_ids.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Years (Select multiple)
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[1, 2, 3, 4].map(year => (
                  <label key={year} className="flex items-center p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      {...register('years', { required: 'At least one year is required' })}
                      type="checkbox"
                      value={year}
                      className="mr-3"
                    />
                    <span className="text-sm font-medium">
                      {year}{year === 1 ? 'st' : year === 2 ? 'nd' : year === 3 ? 'rd' : 'th'} Year
                    </span>
                  </label>
                ))}
              </div>
              {errors.years && (
                <p className="text-red-600 text-sm mt-1">{errors.years.message}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Semester
            </label>
            <div className="grid grid-cols-2 gap-4">
              <label className="flex items-center p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  {...register('semester', { required: 'Semester is required' })}
                  type="radio"
                  value={1}
                  className="sr-only"
                />
                <div className="flex items-center">
                  <div className="w-4 h-4 border-2 border-gray-300 rounded-full mr-3 flex items-center justify-center">
                    <div className="w-2 h-2 bg-gray-900 rounded-full"></div>
                  </div>
                  <span className="text-sm font-medium">1st Semester</span>
                </div>
              </label>
              <label className="flex items-center p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  {...register('semester', { required: 'Semester is required' })}
                  type="radio"
                  value={2}
                  className="sr-only"
                />
                <div className="flex items-center">
                  <div className="w-4 h-4 border-2 border-gray-300 rounded-full mr-3 flex items-center justify-center">
                    <div className="w-2 h-2 bg-gray-900 rounded-full"></div>
                  </div>
                  <span className="text-sm font-medium">2nd Semester</span>
                </div>
              </label>
            </div>
            {errors.semester && (
              <p className="text-red-600 text-sm mt-1">{errors.semester.message}</p>
            )}
          </div>

          <div className="border-t pt-6">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
            >
              <AdjustmentsHorizontalIcon className="h-4 w-4 mr-2" />
              Advanced Algorithm Settings
              <span className="ml-2 text-xs">
                {showAdvanced ? '(Hide)' : '(Show)'}
              </span>
            </button>

            {showAdvanced && (
              <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start gap-3 text-sm text-gray-600 mb-4">
                  <InformationCircleIcon className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  <p>
                    These settings control the genetic algorithm parameters. 
                    Default values work well for most cases.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Population Size
                    </label>
                    <input
                      {...register('population_size', { 
                        min: { value: 10, message: 'Minimum 10' },
                        max: { value: 200, message: 'Maximum 200' }
                      })}
                      type="number"
                      className="input-field"
                      placeholder="50"
                    />
                    <p className="text-xs text-gray-500 mt-1">Number of candidate solutions per generation</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Generations
                    </label>
                    <input
                      {...register('generations', { 
                        min: { value: 50, message: 'Minimum 50' },
                        max: { value: 2000, message: 'Maximum 2000' }
                      })}
                      type="number"
                      className="input-field"
                      placeholder="500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Maximum number of evolution cycles</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Mutation Rate
                    </label>
                    <input
                      {...register('mutation_rate', { 
                        min: { value: 0.01, message: 'Minimum 0.01' },
                        max: { value: 0.5, message: 'Maximum 0.5' }
                      })}
                      type="number"
                      step="0.01"
                      className="input-field"
                      placeholder="0.1"
                    />
                    <p className="text-xs text-gray-500 mt-1">Probability of random changes (0.01-0.5)</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Elite Rate
                    </label>
                    <input
                      {...register('elite_rate', { 
                        min: { value: 0.05, message: 'Minimum 0.05' },
                        max: { value: 0.3, message: 'Maximum 0.3' }
                      })}
                      type="number"
                      step="0.01"
                      className="input-field"
                      placeholder="0.1"
                    />
                    <p className="text-xs text-gray-500 mt-1">Portion of best solutions to preserve (0.05-0.3)</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1 flex items-center justify-center gap-2 py-3"
            >
              {loading ? (
                <>
                  <div className="loading-spinner" />
                  Generating...
                </>
              ) : (
                <>
                  <SparklesIcon className="h-5 w-5" />
                  Generate Timetable
                </>
              )}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="btn-secondary px-6"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>

      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">How it works</h3>
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 bg-gray-900 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
              1
            </div>
            <p>
              The algorithm creates multiple random timetable configurations
            </p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 bg-gray-900 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
              2
            </div>
            <p>
              Each configuration is evaluated for conflicts (instructor, room, student clashes)
            </p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 bg-gray-900 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
              3
            </div>
            <p>
              The best configurations are selected and combined to create improved solutions
            </p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 bg-gray-900 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
              4
            </div>
            <p>
              This process repeats until an optimal conflict-free timetable is found
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
