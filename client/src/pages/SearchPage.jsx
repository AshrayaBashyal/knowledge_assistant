import { MagnifyingGlass, FileText, NotePencil, ChatCircleDots } from '@phosphor-icons/react'
import Card from '../components/ui/Card'

const RESULTS = [
  { type: 'document', id: 1, title: 'budget_report.txt', snippet: 'Q3 travel spend breakdown…' },
  { type: 'note', id: 2, title: 'Budget notes', snippet: 'We discussed cutting travel spend…' },
  { type: 'message', id: 3, title: 'user message', snippet: "What's our budget for…" },
]

const TYPE_META = {
  document: { icon: FileText, tab: 'brass' },
  note: { icon: NotePencil, tab: 'ledger' },
  message: { icon: ChatCircleDots, tab: 'ledger' },
}

export default function SearchPage() {
  return (
    <div>
      <div className="relative mb-6">
        <MagnifyingGlass size={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-soft" />
        <input
          disabled
          defaultValue="budget"
          className="w-full max-w-md rounded-tab border border-mist bg-paper py-2.5 pl-10 pr-3 text-sm text-ink focus:outline-none"
        />
      </div>
      <p className="mb-4 text-sm text-ink-soft">3 results · placeholder data, wired up later</p>

      <div className="space-y-3">
        {RESULTS.map((r) => {
          const meta = TYPE_META[r.type]
          const Icon = meta.icon
          return (
            <Card key={`${r.type}-${r.id}`} tab={meta.tab}>
              <div className="flex items-start gap-3">
                <Icon size={18} className="mt-0.5 text-ink-soft" />
                <div>
                  <p className="font-mono text-[11px] uppercase tracking-wide text-ink-soft">{r.type}</p>
                  <p className="mt-0.5 text-sm font-medium text-ink">{r.title}</p>
                  <p className="mt-1 text-sm text-ink-soft">{r.snippet}</p>
                </div>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}