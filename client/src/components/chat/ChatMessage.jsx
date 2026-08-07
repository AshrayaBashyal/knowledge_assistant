import SourcesList from './SourcesList'
import Spinner from '../ui/Spinner'

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
}

export default function ChatMessage({ message, isStreaming = false }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[75%] min-w-0 ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <p className="font-mono text-[11px] uppercase tracking-wide text-ink-soft">
          {isUser ? 'you' : 'assistant'}
          {message.created_at && ` · ${formatTime(message.created_at)}`}
        </p>

        <div
          className={`rounded-card px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? 'bg-ledger text-paper'
              : 'border border-mist bg-paper-dim text-ink'
          }`}
        >
          {/* Preserve newlines in message content */}
          <p className="whitespace-pre-wrap break-words">{message.content}</p>

          {isStreaming && (
            <span className="ml-1 inline-block">
              <Spinner size={12} className="inline text-ink-soft" />
            </span>
          )}

          {!isUser && message.sources && (
            <SourcesList sources={message.sources} />
          )}
        </div>
      </div>
    </div>
  )
}