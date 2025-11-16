'use client'

import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'

interface TimetableClass {
  course: string
  course_id: string
  instructor: string
  room: string
  section: string
  course_type: string
}

interface TimetableGridProps {
  schedule: Record<string, Record<string, TimetableClass[]>>
  title?: string
}

// ✅ Only Monday–Friday (no Saturday/Sunday)
const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

// Treat 13:00–14:00 as lunch by convention
const LUNCH_START_PREFIX = '13:00'

export default function TimetableGrid({ schedule, title }: TimetableGridProps) {
  const [timeSlots, setTimeSlots] = useState<string[]>([])
  const [courseLegend, setCourseLegend] = useState<{
    course_id: string
    course: string
    instructors: string[]
  }[]>([])

  useEffect(() => {
    // ---- Collect all time slots present in schedule ----
    const allTimeSlots = new Set<string>()

    Object.entries(schedule || {}).forEach(([day, daySchedule]) => {
      if (!days.includes(day)) return // ignore Saturday, etc
      Object.keys(daySchedule || {}).forEach(timeSlot => {
        allTimeSlots.add(timeSlot)
      })
    })

    let slots = Array.from(allTimeSlots)

    // Inject a lunch row if not already present
    const hasLunch = slots.some(slot => slot.startsWith(LUNCH_START_PREFIX))
    if (!hasLunch) {
      // Add a canonical lunch slot; it will still sort correctly
      slots.push('13:00:00-13:45:00')
    }

    // Sort by start time (HH:MM:SS-HH:MM:SS)
    slots.sort((a, b) => {
      const startA = a.split('-')[0]
      const startB = b.split('-')[0]
      return startA.localeCompare(startB)
    })

    setTimeSlots(slots)

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

  const isLunchSlot = (slot: string) => slot.startsWith(LUNCH_START_PREFIX)

  // ---- Drag handlers (UI only, no actual change) ----
  const handleDragStart = (event: React.DragEvent<HTMLDivElement>, cls: TimetableClass) => {
    // Just store something so the browser allows drag
    event.dataTransfer.setData('text/plain', JSON.stringify(cls))
  }

  const handleDragOver = (event: React.DragEvent<HTMLTableCellElement>) => {
    event.preventDefault()
  }

  const handleDrop = (event: React.DragEvent<HTMLTableCellElement>) => {
    event.preventDefault()
    // Show message and do nothing else (no state change)
    toast.error('Timetable is fixed by the genetic algorithm. Manual changes are not allowed.', {
      duration: 4000
    })
  }

  const formatTimeSlotLabel = (slot: string) => {
    const [start, end] = slot.split('-')
    const clean = (t: string) => t.slice(0, 5) // HH:MM from HH:MM:SS
    return `${clean(start)} - ${clean(end)}`
  }

  return (
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
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28 border-b border-r border-gray-200">
                Time
              </th>
              {days.map(day => (
                <th
                  key={day}
                  className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200"
                >
                  {day}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white">
            {timeSlots.map(timeSlot => {
              const lunch = isLunchSlot(timeSlot)
              return (
                <tr key={timeSlot} className="border-t border-gray-200">
                  {/* Time column */}
                  <td className={`px-4 py-3 text-xs font-semibold text-gray-800 bg-gray-50 border-r border-gray-200 whitespace-nowrap ${lunch ? 'text-blue-700' : ''}`}>
                    {formatTimeSlotLabel(timeSlot)}
                    {lunch && <span className="block text-[10px] text-blue-600 mt-1">LUNCH BREAK</span>}
                  </td>

                  {/* Day columns */}
                  {days.map(day => {
                    const dayClasses = schedule[day]?.[timeSlot] || []

                    if (lunch) {
                      // Force lunch row to show lunch block for all days
                      return (
                        <td
                          key={`${day}-${timeSlot}`}
                          className="px-2 py-2 align-middle border-r border-gray-200 bg-blue-50"
                          onDragOver={handleDragOver}
                          onDrop={handleDrop}
                        >
                          <div className="h-full flex items-center justify-center text-[11px] font-semibold text-blue-800 select-none">
                            LUNCH BREAK
                          </div>
                        </td>
                      )
                    }

                    return (
                      <td
                        key={`${day}-${timeSlot}`}
                        className="px-2 py-2 align-top border-r border-gray-200"
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                      >
                        <div className="min-h-[80px] space-y-1">
                          {dayClasses.map((classInfo, index) => (
                            <div
                              key={index}
                              className={`${getCourseTypeColor(classInfo.course_type)} cursor-grab active:cursor-grabbing select-none`}
                              draggable
                              onDragStart={(e) => handleDragStart(e, classInfo)}
                            >
                              <div className="font-semibold text-xs">
                                {classInfo.course_id || classInfo.course}
                              </div>
                              <div className="text-[11px] opacity-90">
                                {classInfo.course}
                              </div>
                              <div className="text-[11px] mt-1 space-y-[2px]">
                                <div>👨‍🏫 {classInfo.instructor}</div>
                                <div>🏠 {classInfo.room}</div>
                                <div>👥 {classInfo.section}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </td>
                    )
                  })}
                </tr>
              )
            })}

            {timeSlots.length === 0 && (
              <tr>
                <td
                  colSpan={days.length + 1}
                  className="text-center py-8 text-gray-500"
                >
                  No classes scheduled
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Legend: Course ↔ Faculty mapping */}
      {courseLegend.length > 0 && (
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">
            Course & Faculty Mapping
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto">
            {courseLegend.map(item => (
              <div
                key={item.course_id || item.course}
                className="flex flex-col text-xs text-gray-800 bg-white rounded-md border border-gray-200 px-3 py-2"
              >
                <span className="font-semibold">
                  {item.course_id && (
                    <span className="mr-1">{item.course_id}</span>
                  )}
                  - {item.course}
                </span>
                <span className="text-[11px] text-gray-600 mt-1">
                  Faculty: {item.instructors.join(', ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
