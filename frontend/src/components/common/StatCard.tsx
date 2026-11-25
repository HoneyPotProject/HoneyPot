import type { ReactNode } from 'react'

export function StatCard({
  label,
  value,
  hint,
  icon,
}: {
  label: string
  value: string | number
  hint?: string
  icon?: ReactNode
}) {
  return (
    <article className="stat-card">
      <div className="stat-card-top">
        <span>{label}</span>
        {icon}
      </div>
      <strong>{value}</strong>
      {hint ? <p>{hint}</p> : null}
    </article>
  )
}
