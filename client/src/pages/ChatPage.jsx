import { useParams } from 'react-router-dom'
import { PaperPlaneTilt } from '@phosphor-icons/react'
import Button from '../components/ui/Button'

// Conversation switching now lives in the sidebar's Chat dropdown, so this
// page only needs to know which conversation (if any) is selected and show
// its thread. Static placeholder message data until Stage 10 wires up the
// real SSE stream and GET /api/chat/conversations/<id>/.
const MESSAGES = [
  { id: 1, role: 'user', content: "What's in the budget report I uploaded?" },
  { id: 2, role: 'assistant', content: 'Give me a moment to look that up for you — this is placeholder text until Stage 10 wires up the real SSE stream.' },
]

export default function ChatPage() {
  const { conversationId } = useParams()

  return (
    <div className="flex h-full flex-col rounded-card border border-mist bg-paper">
      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {!conversationId && (
          <p className="text-sm text-ink-soft">
            New conversation — send a message to start, or pick an existing one from the Chat dropdown in the sidebar.
          </p>
        )}
        {conversationId &&
          MESSAGES.map((m) => (
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
          <PaperPlaneTilt size={16} />
          Send
        </Button>
      </div>
    </div>
  )
}