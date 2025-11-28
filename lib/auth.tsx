'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from './api'
import Cookies from 'js-cookie'

interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_staff: boolean
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = Cookies.get('access_token')
    if (token) {
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchUser = async () => {
    try {
      // ✅ Backend must have this endpoint in views.py -> /api/auth/user/
      const response = await api.get('/auth/user/')
      setUser(response.data)
    } catch (error) {
      // Token might be invalid or expired
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')
      // Rethrow the error so the caller can handle it
      throw error
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    try {
      // ✅ Django SimpleJWT default login endpoint
      const response = await api.post('/auth/token/', {
        username,
        password,
      })

      const { access, refresh } = response.data
      Cookies.set('access_token', access)
      Cookies.set('refresh_token', refresh)

      // Optionally fetch user info after login
      await fetchUser()
    } catch (error: any) {
      // If login fails, ensure we are logged out
      logout()
      throw new Error(error.response?.data?.detail || 'Login failed')
    }
  }

  const logout = () => {
    Cookies.remove('access_token')
    Cookies.remove('refresh_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
