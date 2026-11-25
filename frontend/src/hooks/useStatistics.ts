import { useEffect, useState } from 'react'
import { getStatistics } from '../services/statisticsService'
import type { Statistics } from '../types/statistics'

export function useStatistics(refreshMs = 15000) {
  const [data, setData] = useState<Statistics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = () => {
      const controller = new AbortController()
      getStatistics(controller.signal)
        .then((payload) => {
          if (!cancelled) {
            setData(payload)
            setError(null)
            setLoading(false)
          }
        })
        .catch((err: { message?: string }) => {
          if (!cancelled) {
            setError(err.message || 'Failed to load statistics')
            setLoading(false)
          }
        })
      return controller
    }
    let controller = load()
    const timer = window.setInterval(() => {
      controller.abort()
      controller = load()
    }, refreshMs)
    return () => {
      cancelled = true
      controller.abort()
      window.clearInterval(timer)
    }
  }, [refreshMs])

  return { data, loading, error }
}
