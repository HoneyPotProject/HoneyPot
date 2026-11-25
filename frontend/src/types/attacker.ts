export interface SourceObservation {
  source_ip: string
  first_seen: string
  last_seen: string
  total_events: number
  last_category?: string | null
  category_counts: Record<string, number>
  severity_counts: Record<string, number>
}

export interface SourceListResponse {
  sources: SourceObservation[]
  total: number
  page: number
  page_size: number
}

export interface SourceEvent {
  event_id: string
  timestamp: string
  attack_category: string
  severity: string
  path: string
  method: string
}
