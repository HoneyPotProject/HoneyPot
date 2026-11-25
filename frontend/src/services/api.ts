import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 15000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)
