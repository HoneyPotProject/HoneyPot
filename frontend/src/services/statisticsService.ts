import type { DetectorInfo, Statistics, SystemStatus, TimelinePoint } from '../types/statistics'
import type { SourceListResponse, SourceObservation } from '../types/attacker'
import { api } from './api'

export async function getStatistics(signal?: AbortSignal) {
  const { data } = await api.get<Statistics>('/api/statistics', { signal })
  return data
}

export async function getTimeline(hours = 24, signal?: AbortSignal) {
  const { data } = await api.get<{ timeline: TimelinePoint[] }>('/api/statistics/timeline', {
    params: { hours },
    signal,
  })
  return data.timeline
}

export async function getTopTargets(limit = 8, signal?: AbortSignal) {
  const { data } = await api.get<{ top_targets: { path: string; count: number }[] }>(
    '/api/statistics/top-targets',
    { params: { limit }, signal },
  )
  return data.top_targets
}

export async function getTopSources(limit = 8, signal?: AbortSignal) {
  const { data } = await api.get<{ top_sources: { source_ip: string; count: number }[] }>(
    '/api/statistics/top-sources',
    { params: { limit }, signal },
  )
  return data.top_sources
}

export async function getHourly(signal?: AbortSignal) {
  const { data } = await api.get<{ hourly: { hour: number; count: number }[] }>(
    '/api/statistics/hourly',
    { signal },
  )
  return data.hourly
}

export async function getDetectors(signal?: AbortSignal) {
  const { data } = await api.get<{ detectors: DetectorInfo[]; total: number }>('/api/detectors', {
    signal,
  })
  return data
}

export async function getSystemStatus(signal?: AbortSignal) {
  const { data } = await api.get<SystemStatus>('/api/system/status', { signal })
  return data
}

export async function getSources(page = 1, signal?: AbortSignal) {
  const { data } = await api.get<SourceListResponse>('/api/attackers', {
    params: { page, page_size: 50 },
    signal,
  })
  return data
}

export async function getSource(ip: string, signal?: AbortSignal) {
  const { data } = await api.get<SourceObservation>(`/api/attackers/${encodeURIComponent(ip)}`, {
    signal,
  })
  return data
}

export async function getSourceEvents(ip: string, page = 1, signal?: AbortSignal) {
  const { data } = await api.get<{ events: Array<{
    event_id: string
    timestamp: string
    attack_category: string
    severity: string
    path: string
    method: string
  }>; total: number }>(`/api/attackers/${encodeURIComponent(ip)}/events`, {
    params: { page, page_size: 20 },
    signal,
  })
  return data
}

export async function getSourceTimeline(ip: string, signal?: AbortSignal) {
  const { data } = await api.get<{ timeline: TimelinePoint[] }>(
    `/api/attackers/${encodeURIComponent(ip)}/timeline`,
    { signal },
  )
  return data.timeline
}

export async function login(username: string, password: string) {
  const { data } = await api.post('/api/auth/login', { username, password })
  return data as { status: string; username: string }
}

export async function logout() {
  await api.post('/api/auth/logout')
}

export async function me() {
  const { data } = await api.get<{ username: string; role: string }>('/api/auth/me')
  return data
}
