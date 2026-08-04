export default function EmptyState({ icon, title, hint, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-card border border-dashed border-mist-dim px-6 py-16 text-center">
      {icon && <div className="text-ink-soft/60">{icon}</div>}
      <p className="font-display italic text-xl text-ink">{title}</p>
      {hint && <p className="max-w-sm text-sm text-ink-soft">{hint}</p>}
      {action}
    </div>
  )
}