type MetricCardProps = {
  label: string
  value: string
  meta: string
  accent: string
}

export function MetricCard({ label, value, meta, accent }: MetricCardProps) {
  return (
    <article className="metric-card" style={{ ['--metric-accent' as string]: accent }}>
      <div className="metric-card__label">{label}</div>
      <div className="metric-card__value">{value}</div>
      <div className="metric-card__meta">{meta}</div>
    </article>
  )
}
