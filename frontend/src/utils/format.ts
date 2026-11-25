export function formatTimestamp(value?: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function formatCategory(value: string) {
  return value.replaceAll('_', ' ')
}

export function severityClass(severity: string) {
  switch (severity) {
    case 'critical':
      return 'sev-critical'
    case 'high':
      return 'sev-high'
    case 'medium':
      return 'sev-medium'
    default:
      return 'sev-low'
  }
}
