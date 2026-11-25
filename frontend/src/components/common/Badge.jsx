import { formatCategory, severityClass } from '../../utils/format'

export function SeverityBadge({ value }) {
  return <span className={`badge ${severityClass(value)}`}>{value}</span>
}

export function CategoryBadge({ value }) {
  return <span className="badge badge-cat">{formatCategory(value)}</span>
}
