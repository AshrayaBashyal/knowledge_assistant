import { PaperPlaneTiltIcon } from '@phosphor-icons/react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

const CONVERSATIONS = [
  { id: 1, title: 'Budget report questions', updated: '2h ago' },
  { id: 2, title: 'New Conversation', updated: '1d ago' },
]

const MESSAGES = [
  { id: 1, role: 'user', content: "What's in the budget report I uploaded?" },
  { id: 2, role: 'assistant', content: 'Give me a moment to look that up for you — this is placeholder text until the real SSE stream.' },
]

export default function ChatPage() {
  return (
    <div className="flex h-full gap-6">
      <div className="w-64 shrink-0 space-y-2">
        <Button variant="ghost" className="w-full justify-center">New conversation</Button>
        {CONVERSATIONS.map((c) => (
          <Card key={c.id} tab="ledger" className="cursor-pointer">
            <p className="truncate text-sm text-ink">{c.title}</p>
            <p className="mt-1 font-mono text-[11px] text-ink-soft">{c.updated}</p>
          </Card>
        ))}
      </div>

      <div className="flex flex-1 flex-col rounded-card border border-mist bg-paper">
        <div className="flex-1 space-y-4 overflow-y-auto p-6">
          {MESSAGES.map((m) => (
            <div key={m.id} className={`max-w-lg ${m.role === 'user' ? 'ml-auto text-right' : ''}`}>
              <p className="mb-1 font-mono text-[11px] uppercase tracking-wide text-ink-soft">
                {m.role === 'user' ? 'you' : 'assistant'}
              </p>
              <div
                className={`inline-block rounded-card px-4 py-2.5 text-sm ${
                  m.role === 'user' ? 'bg-ledger text-paper' : 'border border-mist bg-paper-dim text-ink'
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-3 border-t border-mist p-4">
          <input
            disabled
            placeholder="Message the assistant… (wired up in Stage 10)"
            className="flex-1 rounded-tab border border-mist bg-paper px-3 py-2 text-sm text-ink-soft placeholder:text-ink-soft focus:outline-none"
          />
          <Button disabled>
            <PaperPlaneTiltIcon size={16} />
            Send
          </Button>
        </div>
      </div>
    </div>
  )
}