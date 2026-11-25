import { formatCategory, severityClass } from '../../utils/format'

export function SeverityBadge({ value }: { value: string }) {
  return <span className={`badge ${severityClass(value)}`}>{value}</span>
}

export function CategoryBadge({ value }: { value: string }) {
  return <span className="badge badge-cat">{formatCategory(value)}</span>
}
