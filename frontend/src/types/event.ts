export type Severity = 'low' | 'medium' | 'high' | 'critical'
export type InvestigationStatus = 'new' | 'under_review' | 'reviewed' | 'false_positive'

export interface SecurityEvent {
  event_id: string
  source_ip: string
  timestamp: string
  attack_category: string
  severity: Severity | string
  confidence: number
  detector_names: string[]
  detection_reasons: string[]
  evidence: Record<string, unknown>
  target: string
  method: string
  path: string
  request_id?: string | null
  metadata: Record<string, unknown>
  related_events?: RelatedEvent[]
  annotations?: Annotation[]
  investigation_status?: InvestigationStatus | string
}

export interface RelatedEvent {
  event_id: string
  timestamp: string
  attack_category: string
  severity: string
  path: string
}

export interface Annotation {
  id: number
  status: string
  notes?: string | null
  analyst_id: string
  created_at: string
  updated_at: string
}

export interface EventListResponse {
  events: SecurityEvent[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface EventFilters {
  page?: number
  page_size?: number
  source_ip?: string
  severity?: string
  attack_category?: string
  start_time?: string
  end_time?: string
  search?: string
  sort_by?: string
  sort_dir?: string
}
