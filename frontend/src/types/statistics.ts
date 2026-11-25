export interface Statistics {
  total_events: number
  unique_sources: number
  critical_events: number
  high_severity_events: number
  events_last_24h: number
  enabled_detectors: number
  category_distribution: Record<string, number>
  severity_distribution: Record<string, number>
}

export interface TimelinePoint {
  time: string
  count: number
}

export interface DetectorInfo {
  name: string
  category: string
  description: string
  enabled: boolean
  detection_count: number
  version: string
}

export interface SystemStatus {
  backend_status: string
  engine_running: boolean
  honeypot_running?: boolean
  database_status: string
  queue_depth: number
  queue_capacity: number
  processed_events: number
  dropped_events: number
  processing_errors: number
  last_processed_event: string | null
  ws_connections: number
  uptime_seconds: number
  honeypot_port: number
  queue_utilization?: number
}
