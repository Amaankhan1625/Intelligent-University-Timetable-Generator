import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CoursesPage from '../page'
import { rest } from 'msw'
import { setupServer } from 'msw/node'

const courseList = [
  {
    id: 1,
    course_id: 'CS101',
    course_name: 'Intro to CS',
    course_type: 'Theory',
    credits: 3,
    max_students: 50,
    duration: 1,
    classes_per_week: 3,
    year: 1
  },
  {
    id: 3,
    course_id: 'CS102',
    course_name: 'Intermediate CS',
    course_type: 'Theory',
    credits: 3,
    max_students: 40,
    duration: 1,
    classes_per_week: 3,
    year: 1
  },
  {
    id: 2,
    course_id: 'CS201',
    course_name: 'Data Structures',
    course_type: 'Theory',
    credits: 4,
    max_students: 45,
    duration: 1,
    classes_per_week: 3,
    year: 2
  }
]

const server = setupServer(
  rest.get('/api/courses/', (req, res, ctx) => {
    return res(ctx.json(courseList))
  }),
  rest.post('/api/courses/', (req, res, ctx) => {
    return res(ctx.status(201), ctx.json({ id: 3, ...req.body }))
  }),
  rest.put('/api/courses/:id/', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(req.body))
  }),
  rest.delete('/api/courses/:id/', (req, res, ctx) => {
    return res(ctx.status(204))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('CoursesPage', () => {
  test('fetches and displays courses sorted by year', async () => {
    render(<CoursesPage />)

    await waitFor(() => {
      expect(screen.getByText('CS101')).toBeInTheDocument()
      expect(screen.getByText('CS102')).toBeInTheDocument()
      expect(screen.getByText('CS201')).toBeInTheDocument()
    })

    const rows = screen.getAllByRole('row')
    // Header + 3 data rows
    expect(rows).toHaveLength(4)

    // Check sorting by year ascending
    const firstYearCell = screen.getAllByText('1')
    const secondYearCell = screen.getAllByText('2')[0]
    expect(firstYearCell.length).toBe(2)  // two courses in year 1
    expect(secondYearCell).toBeInTheDocument()

    // Check sorting within the same year by course number ascending: CS101 then CS102
    const courseIdCells = screen.getAllByText(/CS\d+/)
    const firstCourseIndex = courseIdCells.findIndex(cell => cell.textContent === 'CS101')
    const secondCourseIndex = courseIdCells.findIndex(cell => cell.textContent === 'CS102')
    expect(firstCourseIndex).toBeLessThan(secondCourseIndex)
  })

  test('creates a new course with year', async () => {
    render(<CoursesPage />)

    // Open modal
    userEvent.click(screen.getByRole('button', { name: /Add Course/i }))

    // Fill form fields
    userEvent.type(screen.getByLabelText(/Course ID/i), 'CS301')
    userEvent.type(screen.getByLabelText(/Course Name/i), 'Algorithms')
    userEvent.selectOptions(screen.getByLabelText(/Course Type/i), ['Theory'])
    userEvent.type(screen.getByLabelText(/Credits/i), '3')
    userEvent.type(screen.getByLabelText(/Max Students/i), '60')
    userEvent.type(screen.getByLabelText(/Duration/i), '1')
    userEvent.type(screen.getByLabelText(/Classes per Week/i), '3')
    userEvent.selectOptions(screen.getByLabelText(/Year/i), ['3'])

    // Submit form
    userEvent.click(screen.getByRole('button', { name: /Create Course/i }))

    await waitFor(() => {
      expect(screen.getByText('CS301')).toBeInTheDocument()
    })
  })

  test('edits a course year', async () => {
    render(<CoursesPage />)

    await waitFor(() => screen.getByText('CS101'))

    // Click edit for first course
    userEvent.click(screen.getAllByRole('button', { name: /Edit/i })[0])

    // Change year
    userEvent.selectOptions(screen.getByLabelText(/Year/i), ['4'])

    // Submit update
    userEvent.click(screen.getByRole('button', { name: /Update Course/i }))

    await waitFor(() => {
      expect(screen.getAllByText('4')[0]).toBeInTheDocument()
    })
  })

  test('deletes a course', async () => {
    global.confirm = jest.fn(() => true) // Mock confirm dialog to 'OK'
    render(<CoursesPage />)

    await waitFor(() => screen.getByText('CS101'))

    // Click delete for first course
    userEvent.click(screen.getAllByRole('button', { name: /Delete/i })[0])

    await waitFor(() => {
      expect(screen.queryByText('CS101')).not.toBeInTheDocument()
    })
  })
})
