import { useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import {
  FileText, NotePencil, Brain, MagnifyingGlass, Cards,
  ChatCircleDots, CaretDown, PencilSimpleLine, Trash,
} from '@phosphor-icons/react'
import Logo from '../Logo'
import { useConversations } from '../../lib/ConversationsContext'

const NAV_ITEMS = [
  { to: '/documents', label: 'Documents', icon: FileText },
  { to: '/notes', label: 'Notes', icon: NotePencil },
  { to: '/memory', label: 'Memory', icon: Brain },
  { to: '/search', label: 'Search', icon: MagnifyingGlass },
  { to: '/flashcards', label: 'Flashcards', icon: Cards },
]

function NavTab({ isActive }) {
  return (
    <span
      aria-hidden="true"
      className={`absolute -left-3 top-1/2 h-5 w-1.5 -translate-y-1/2 rounded-tab-sm transition-opacity ${
        isActive ? 'bg-brass opacity-100' : 'opacity-0'
      }`}
    />
  )
}

export default function Sidebar({ onNavClick }) {
  const location = useLocation()
  const navigate = useNavigate()
  const onChatRoute = location.pathname.startsWith('/chat')
  const [chatOpen, setChatOpen] = useState(onChatRoute)
  const { conversations, loading, removeConversation } = useConversations()

  async function handleDeleteConversation(e, id) {
    // Stop the click from also navigating into the conversation.
    e.preventDefault()
    e.stopPropagation()
    try {
      await removeConversation(id)
      // If we just deleted the conversation we're currently viewing, go home.
      if (location.pathname === `/chat/${id}`) {
        navigate('/chat', { replace: true })
      }
    } catch {
      // silently ignore - the page itself will handle errors for the active conversation
    }
  }

  return (
    <aside className="flex h-full w-60 shrink-0 flex-col overflow-hidden border-r border-mist bg-paper-dim">
      <div className="flex items-center gap-2.5 px-5 py-6">
        <Logo size={26} />
        <span className="font-display italic text-2xl leading-none text-ink">Reading Room</span>
      </div>

      <div className="px-3 pb-3">
        <NavLink
          to="/chat"
          onClick={onNavClick}
          className="flex items-center justify-center gap-2 rounded-tab bg-ledger py-2.5 text-sm font-medium text-paper transition-colors hover:bg-ledger-dim"
        >
          <PencilSimpleLine size={17} />
          New chat
        </NavLink>
      </div>

      <nav className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto px-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavClick}
            className={({ isActive }) =>
              `group relative flex items-center gap-3 rounded-tab py-2.5 pl-4 pr-3 text-sm font-body transition-colors ${
                isActive ? 'text-ink' : 'text-ink-soft hover:text-ink'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <NavTab isActive={isActive} />
                <Icon size={19} weight={isActive ? 'duotone' : 'regular'} />
                <span className={isActive ? 'font-medium' : ''}>{label}</span>
              </>
            )}
          </NavLink>
        ))}

        {/* Chat dropdown - sits last so it expands downward into empty space */}
        <div className="mt-auto pt-1">
          <button
            type="button"
            onClick={() => setChatOpen((o) => !o)}
            className={`group relative flex w-full items-center gap-3 rounded-tab py-2.5 pl-4 pr-3 text-sm font-body transition-colors ${
              onChatRoute ? 'text-ink' : 'text-ink-soft hover:text-ink'
            }`}
            aria-expanded={chatOpen}
          >
            <NavTab isActive={onChatRoute} />
            <ChatCircleDots size={19} weight={onChatRoute ? 'duotone' : 'regular'} />
            <span className={`flex-1 text-left ${onChatRoute ? 'font-medium' : ''}`}>Chat</span>
            <CaretDown size={14} className={`transition-transform ${chatOpen ? 'rotate-180' : ''}`} />
          </button>

          {chatOpen && (
            <div className="ml-4 mt-1 space-y-0.5 border-l border-mist pl-3">
              {loading && (
                <p className="py-1 pl-2 font-mono text-[11px] text-ink-soft">Loading…</p>
              )}
              {!loading && conversations.length === 0 && (
                <p className="py-1 pl-2 font-mono text-[11px] text-ink-soft">No conversations yet</p>
              )}
              {conversations.map((c) => (
                <NavLink
                  key={c.id}
                  to={`/chat/${c.id}`}
                  className={({ isActive }) =>
                    `group/convo flex items-center justify-between rounded-tab py-1.5 pl-2 pr-1 text-xs transition-colors ${
                      isActive ? 'bg-paper text-ink font-medium' : 'text-ink-soft hover:text-ink'
                    }`
                  }
                >
                  <span className="min-w-0 flex-1 truncate">{c.title || 'New Conversation'}</span>
                  <button
                    onClick={(e) => handleDeleteConversation(e, c.id)}
                    className="ml-1 shrink-0 rounded p-0.5 opacity-0 transition-opacity hover:text-crimson group-hover/convo:opacity-100 touch:opacity-100"
                    title="Delete"
                  >
                    <Trash size={12} />
                  </button>
                </NavLink>
              ))}
            </div>
          )}
        </div>
      </nav>

      <div className="border-t border-mist px-5 py-4 font-mono text-[11px] text-ink-soft">
        v0.1 — stage 10
      </div>
    </aside>
  )
}