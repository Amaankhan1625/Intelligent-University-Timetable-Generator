import axios from 'axios'
import Cookies from 'js-cookie'

// ✅ Ensure this matches Django backend URL pattern
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
})

// --------------------
// REQUEST INTERCEPTOR
// --------------------
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// --------------------
// RESPONSE INTERCEPTOR
// --------------------
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // If 401, attempt to refresh the token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = Cookies.get('refresh_token')
      if (refreshToken) {
        try {
          // ✅ Use Django SimpleJWT refresh endpoint
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          })

          const { access } = response.data
          Cookies.set('access_token', access)
          originalRequest.headers.Authorization = `Bearer ${access}`

          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed, clear tokens and reject
          Cookies.remove('access_token')
          Cookies.remove('refresh_token')
          // window.location.href = '/login' // <-- REMOVED
          return Promise.reject(refreshError) // <-- ADDED
        }
      } else {
        // No refresh token, just reject
        // window.location.href = '/login' // <-- REMOVED
        return Promise.reject(error) // <-- ADDED
      }
    }

    return Promise.reject(error)
  }
)
