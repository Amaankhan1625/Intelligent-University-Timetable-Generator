import React from 'react'
import '@testing-library/jest-dom'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import InstructorsPage from '../page'
import { rest } from 'msw'
import { setupServer } from 'msw/node'

const instructorsList = [
  {
    id: 1,
    instructor_id: 'I101',
    name: 'John Doe',
    email: 'john.doe@example.com',
    is_available: true
  },
  {
    id: 2,
    instructor_id: 'I102',
    name: 'Jane Smith',
    email: 'jane.smith@example.com',
    is_available: false
  }
]

const server = setupServer(
  rest.get('/api/instructors/', (req, res, ctx) => {
    return res(ctx.json(instructorsList))
  }),
  rest.post('/api/instructors/', (req, res, ctx) => {
    return res(ctx.status(201), ctx.json({ id: 3, ...req.body }))
  }),
  rest.put('/api/instructors/:id/', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(req.body))
  }),
  rest.delete('/api/instructors/:id/', (req, res, ctx) => {
    return res(ctx.status(204))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('InstructorsPage', () => {
  test('fetches and displays instructors', async () => {
    render(<InstructorsPage />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
    })
  })

  // Additional tests for create/edit/delete can be added here similarly as needed.
})
