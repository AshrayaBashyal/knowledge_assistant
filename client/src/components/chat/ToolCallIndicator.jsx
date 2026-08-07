import { MagnifyingGlass, Calculator, Clock, Brain, Globe } from '@phosphor-icons/react'
import Spinner from '../ui/Spinner'

const TOOL_META = {
  search_my_knowledge: { label: 'Searching your knowledge…', Icon: MagnifyingGlass },
  remember_fact: { label: 'Saving a fact…', Icon: Brain },
  calculator: { label: 'Calculating…', Icon: Calculator },
  current_time: { label: 'Checking the time…', Icon: Clock },
  tavily_search: { label: 'Searching the web…', Icon: Globe },
}

export default function ToolCallIndicator({ tools, sources }) {
  if (!tools.length) return null

  const lastTool = tools[tools.length - 1]
  const meta = TOOL_META[lastTool] ?? { label: `Using ${lastTool}…`, Icon: Spinner }
  const Icon = meta.Icon

  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2 text-xs text-ink-soft">
        <Spinner size={13} />
        <Icon size={13} />
        <span className="font-mono">{meta.label}</span>
      </div>

      {sources && sources.length > 0 && (
        <div className="ml-6 space-y-0.5">
          {sources.map((s, i) => (
            <p key={i} className="font-mono text-[11px] text-ink-soft">
              ↳ {s.title}{' '}
              <span className="text-mist-dim">({s.source_type})</span>
            </p>
          ))}
        </div>
      )}
    </div>
  )
}