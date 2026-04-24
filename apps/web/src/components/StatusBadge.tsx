type StatusTone = 'ok' | 'warn' | 'critical' | 'info' | 'muted'

type StatusBadgeProps = {
  label: string
  tone?: StatusTone
}

export function StatusBadge({ label, tone = 'info' }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`}>{label}</span>
}
