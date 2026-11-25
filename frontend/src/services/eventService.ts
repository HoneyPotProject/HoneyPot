import type { EventFilters, EventListResponse, SecurityEvent } from '../types/event'
import { api } from './api'

export async function getEvents(filters: EventFilters = {}, signal?: AbortSignal) {
  const { data } = await api.get<EventListResponse>('/api/events', { params: filters, signal })
  return data
}

export async function getEvent(eventId: string, signal?: AbortSignal) {
  const { data } = await api.get<SecurityEvent>(`/api/events/${eventId}`, { signal })
  return data
}

export async function annotateEvent(
  eventId: string,
  payload: { status: string; notes?: string },
) {
  const { data } = await api.post(`/api/events/${eventId}/annotation`, payload)
  return data
}

export function eventsExportUrl(filters: EventFilters = {}) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, String(value))
  })
  const base = api.defaults.baseURL || ''
  return `${base}/api/events/export?${params.toString()}`
}
