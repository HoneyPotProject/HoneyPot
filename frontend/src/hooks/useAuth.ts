import { useCallback, useEffect, useState } from 'react'
import { login as loginRequest, logout as logoutRequest, me } from '../services/statisticsService'

export function useAuth() {
  const [username, setUsername] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    me()
      .then((data) => {
        if (!cancelled) setUsername(data.username)
      })
      .catch(() => {
        if (!cancelled) setUsername(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (user: string, password: string) => {
    const data = await loginRequest(user, password)
    setUsername(data.username)
  }, [])

  const logout = useCallback(async () => {
    await logoutRequest()
    setUsername(null)
    window.location.href = '/login'
  }, [])

  return { username, loading, isAuthenticated: Boolean(username), login, logout }
}
