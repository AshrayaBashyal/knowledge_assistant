import { FileText, NotePencil, Brain } from '@phosphor-icons/react'

const SOURCE_ICON = {
  document: FileText,
  note: NotePencil,
  memory: Brain,
}

export default function SourcesList({ sources }) {
  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-2 space-y-1 border-t border-mist pt-2">
      <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">Sources</p>
      {sources.map((s, i) => {
        const Icon = SOURCE_ICON[s.source_type] ?? FileText
        return (
          <div key={i} className="flex items-center gap-2">
            <Icon size={12} className="shrink-0 text-ink-soft" />
            <p className="font-mono text-[11px] text-ink-soft">{s.title}</p>
          </div>
        )
      })}
    </div>
  )
}