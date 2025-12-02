'use client'

import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'

interface TimetableClass {
  class_id: string
  course: string
  course_id: string
  instructor: string
  room: string
  section: string
  course_type: string
  duration?: number
  is_start?: boolean
  colspan?: number
}

interface TimetableGridProps {
  schedule: Record<string, Record<string, TimetableClass[]>>
  title?: string
  editMode?: boolean
  onSlotUpdate?: (classId: string, newDay: string, newTime: string) => Promise<void>
}

// ✅ Only Monday–Friday (no Saturday/Sunday)
const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

// Exact canonical lunch slot we will use: 13:00–13:45
const LUNCH_SLOT = '13:00:00-13:45:00'

export default function TimetableGrid({ schedule, title, editMode, onSlotUpdate }: TimetableGridProps) {
  const [timeSlots, setTimeSlots] = useState<string[]>([])
  const [courseLegend, setCourseLegend] = useState<{
    course_id: string
    course: string
    instructors: string[]
  }[]>([])
  const [selectedClass, setSelectedClass] = useState<TimetableClass | null>(null)

  useEffect(() => {
    // ---- Use standard consecutive time slots based on meeting times ----
    const standardTimeSlots = [
      '09:00:00-10:00:00',
      '10:00:00-11:00:00',
      '11:00:00-12:00:00',
      '12:00:00-13:00:00',
      '13:00:00-13:45:00', // Lunch break
      '13:45:00-14:45:00',
      '14:45:00-15:45:00',
      '15:45:00-16:45:00'
    ]

    setTimeSlots(standardTimeSlots)

    // ---- Build course legend (unique courses with instructors) ----
    const legendMap = new Map<string, { course_id: string; course: string; instructors: Set<string> }>()

    Object.entries(schedule || {}).forEach(([day, daySchedule]) => {
      if (!days.includes(day)) return
      Object.values(daySchedule || {}).forEach(classesAtSlot => {
        classesAtSlot.forEach((cls: TimetableClass) => {
          const key = cls.course_id || cls.course
          if (!legendMap.has(key)) {
            legendMap.set(key, {
              course_id: cls.course_id,
              course: cls.course,
              instructors: new Set([cls.instructor])
            })
          } else {
            legendMap.get(key)!.instructors.add(cls.instructor)
          }
        })
      })
    })

    const legend = Array.from(legendMap.values()).map(item => ({
      course_id: item.course_id,
      course: item.course,
      instructors: Array.from(item.instructors)
    }))

    setCourseLegend(legend)
  }, [schedule])

  const getCourseTypeColor = (courseType: string) => {
    const type = (courseType || '').toLowerCase()
    switch (type) {
      case 'lab':
        return 'timetable-cell lab'
      case 'theory':
        return 'timetable-cell theory'
      case 'practical':
        return 'timetable-cell practical'
      default:
        return 'timetable-cell'
    }
  }

  const isLunchSlot = (slot: string) => {
    const [start, end] = slot.split('-')
    return start === '13:00:00' && end === '13:45:00'
  }

  const handleClassClick = (classData: TimetableClass) => {
    if (!editMode) {
      toast.error('Enable edit mode to move classes')
      return
    }
    setSelectedClass(classData)
    toast.success(`Selected ${classData.course}. Now click on an empty slot to move it.`)
  }

  const handleSlotClick = async (day: string, timeSlot: string) => {
    if (!editMode || !selectedClass) return

    // Don't allow moving to lunch slots
    if (isLunchSlot(timeSlot)) {
      toast.error('Cannot move classes to lunch break slots')
      return
    }

    // Check if the slot is already occupied
    const existingClasses = schedule[day]?.[timeSlot] || []
    if (existingClasses.length > 0) {
      toast.error('This slot is already occupied. Please choose an empty slot.')
      return
    }

    try {
      console.log('Moving class:', selectedClass.class_id, 'to', day, timeSlot)

      // Call the onSlotUpdate callback with the new slot information
      await onSlotUpdate?.(selectedClass.class_id, day, timeSlot)

      toast.success(`Moved ${selectedClass.course} to ${day} ${formatTimeSlotLabel(timeSlot)}`)
      setSelectedClass(null)
    } catch (error) {
      console.error('Error moving class:', error)
      toast.error('Failed to move class - check console for details')
    }
  }

  const cancelSelection = () => {
    setSelectedClass(null)
    toast.success('Selection cancelled')
  }

  const formatTimeSlotLabel = (slot: string) => {
    const [start, end] = slot.split('-')
    const clean = (t: string) => t.slice(0, 5) // HH:MM from HH:MM:SS
    return `${clean(start)} - ${clean(end)}`
  }

  return (
    <div className="space-y-6">
      {editMode && selectedClass && (
        <div className="card p-4 bg-green-50 border-green-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-green-800">
              <strong>Selected Class:</strong> {selectedClass.course} ({selectedClass.instructor})
              <br />
              <span className="text-xs">Click on an empty slot to move this class there.</span>
            </div>
            <button
              onClick={cancelSelection}
              className="btn-secondary text-xs"
            >
              Cancel Selection
            </button>
          </div>
        </div>
      )}

      {/* First Table: Schedule Grid */}
      <div className="card overflow-hidden">
        {title && (
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24 border-b border-r border-gray-200">
                  Day
                </th>
                {timeSlots.map(timeSlot => (
                  <th
                    key={timeSlot}
                    className={`px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200 ${isLunchSlot(timeSlot) ? 'text-blue-700' : ''}`}
                  >
                    {formatTimeSlotLabel(timeSlot)}
                    {isLunchSlot(timeSlot) && <span className="block text-[10px] text-blue-600 mt-1">LUNCH</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white">
              {days.map(day => (
                <tr key={day} className="border-t border-gray-200">
                  {/* Day column */}
                  <td className="px-2 py-2 text-xs font-semibold text-gray-800 bg-gray-50 border-r border-gray-200 whitespace-nowrap">
                    {day}
                  </td>

                  {/* Time columns */}
                  {timeSlots.map((timeSlot, slotIndex) => {
                    const dayClasses = schedule[day]?.[timeSlot] || []
                    const lunch = isLunchSlot(timeSlot)

                    if (lunch) {
                      // Force lunch column to show lunch block for all days
                      return (
                        <td
                          key={`${day}-${timeSlot}`}
                          className="px-2 py-2 align-middle border-r border-gray-200 bg-blue-50"
                        >
                          <div className="h-full flex items-center justify-center text-[11px] font-semibold text-blue-800 select-none">
                            LUNCH BREAK
                          </div>
                        </td>
                      )
                    }

                    // Check if this slot should be skipped due to colspan from previous multi-hour class
                    const previousSlots = timeSlots.slice(0, slotIndex)
                    let skipSlot = false
                    for (const prevSlot of previousSlots) {
                      const prevClasses = schedule[day]?.[prevSlot] || []
                      for (const prevClass of prevClasses) {
                        if (prevClass.is_start && prevClass.colspan && prevClass.colspan > 1) {
                          const startIndex = timeSlots.indexOf(prevSlot)
                          const endIndex = startIndex + prevClass.colspan - 1
                          if (slotIndex <= endIndex) {
                            skipSlot = true
                            break
                          }
                        }
                      }
                      if (skipSlot) break
                    }

                    if (skipSlot) {
                      return null
                    }

                    // Check if there's a multi-hour class starting at this slot
                    const multiHourClass = dayClasses.find(cls => cls.is_start && cls.colspan && cls.colspan > 1)

                    return (
                      <td
                        key={`${day}-${timeSlot}`}
                        className={`px-2 py-2 align-top border-r border-gray-200 ${editMode && !dayClasses.length ? 'cursor-pointer hover:bg-blue-50' : ''}`}
                        colSpan={multiHourClass ? multiHourClass.colspan : 1}
                        onClick={() => editMode && !dayClasses.length && handleSlotClick(day, timeSlot)}
                      >
                        <div className="min-h-[60px] space-y-1">
                          {dayClasses.map((classInfo, index) => (
                            <div
                              key={index}
                              className={`${getCourseTypeColor(classInfo.course_type)} ${editMode ? 'cursor-pointer hover:ring-2 hover:ring-blue-300' : ''} select-none`}
                              onClick={() => editMode && handleClassClick(classInfo)}
                            >
                              <div className="font-semibold text-xs">
                                {classInfo.course}
                              </div>
                              {multiHourClass && classInfo.is_start && (
                                <div className="text-[10px] text-gray-600 mt-1">
                                  {formatTimeSlotLabel(timeSlot)} - {formatTimeSlotLabel(timeSlots[slotIndex + (classInfo.colspan || 1) - 1])}
                                </div>
                              )}
                              <div className="text-[10px] text-gray-600 mt-1">
                                {classInfo.room && `Room: ${classInfo.room}`}
                              </div>
                              <div className="text-[10px] text-gray-600">
                                {classInfo.instructor}
                              </div>
                            </div>
                          ))}
                          {editMode && !dayClasses.length && (
                            <div className="text-center text-gray-400 text-xs py-4">
                              Click to place selected class
                            </div>
                          )}
                        </div>
                      </td>
                    )
                  })}
                </tr>
              ))}

              {days.length === 0 && (
                <tr>
                  <td
                    colSpan={timeSlots.length + 1}
                    className="text-center py-8 text-gray-500"
                  >
                    No classes scheduled
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Second Table: Instructor Information */}
      {courseLegend.length > 0 && (
        <div className="card overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900">Instructor Information</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-r border-gray-200">
                    Instructor
                  </th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                    Courses & Course Codes
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {courseLegend.map(item => (
                  <tr key={item.course_id || item.course} className="border-t border-gray-200">
                    <td className="px-2 py-2 text-xs font-medium text-gray-900 border-r border-gray-200">
                      {item.instructors.join(', ')}
                    </td>
                    <td className="px-2 py-2 text-xs text-gray-700">
                      <div className="space-y-1">
                        <div className="font-semibold">
                          {item.course_id && (
                            <span className="mr-2 text-blue-600">{item.course_id}</span>
                          )}
                          {item.course}
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

