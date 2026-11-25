import { useEffect, useState } from 'react'
import { getEvents } from '../services/eventService'
import type { EventFilters, EventListResponse } from '../types/event'

export function useEvents(filters: EventFilters) {
  const [data, setData] = useState<EventListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    getEvents(filters, controller.signal)
      .then((payload) => {
        setData(payload)
        setError(null)
      })
      .catch((err: { name?: string; message?: string }) => {
        if (err.name !== 'CanceledError' && err.name !== 'AbortError') {
          setError(err.message || 'Failed to load events')
        }
      })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [
    filters.page,
    filters.page_size,
    filters.search,
    filters.severity,
    filters.attack_category,
    filters.source_ip,
    filters.start_time,
    filters.end_time,
    filters.sort_by,
    filters.sort_dir,
  ])

  return { data, loading, error }
}
