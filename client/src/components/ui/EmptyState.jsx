export default function EmptyState({ icon, title, hint, action }) {
  return (
    <div
      role="status"
      className="flex flex-col items-center justify-center gap-3 rounded-card border border-dashed border-mist-dim px-6 py-20 text-center"
    >
      {icon && <div className="mb-1 text-ink-soft/50">{icon}</div>}
      <p className="font-display italic text-xl text-ink">{title}</p>
      {hint && <p className="max-w-sm text-sm leading-relaxed text-ink-soft">{hint}</p>}
      {action && <div className="mt-1">{action}</div>}
    </div>
  )
}