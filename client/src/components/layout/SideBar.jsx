import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  FileText,
  NotePencil,
  Brain,
  MagnifyingGlass,
  Cards,
  ChatCircleDots,
  CaretDown,
  PencilSimpleLine,
} from '@phosphor-icons/react'
import Logo from '../Logo'

// Everything except Chat - a plain, non-expanding nav item each.
const NAV_ITEMS = [
  { to: '/documents', label: 'Documents', icon: FileText },
  { to: '/notes', label: 'Notes', icon: NotePencil },
  { to: '/memory', label: 'Memory', icon: Brain },
  { to: '/search', label: 'Search', icon: MagnifyingGlass },
  { to: '/flashcards', label: 'Flashcards', icon: Cards },
]

// Placeholder data until later fetch GET /api/chat/conversations/ for real.
const CONVERSATIONS = [
  { id: 1, title: 'Budget report questions' },
  { id: 2, title: 'New Conversation' },
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

export default function Sidebar() {
  const location = useLocation()
  const onChatRoute = location.pathname.startsWith('/chat')
  // Auto-open the conversation list whenever we're already on a chat route,
  // e.g. after following a link straight to /chat/5.
  const [chatOpen, setChatOpen] = useState(onChatRoute)

  return (
    <aside className="flex h-full w-60 shrink-0 flex-col overflow-hidden border-r border-mist bg-paper-dim">
      <div className="flex items-center gap-2.5 px-5 py-6">
        <Logo size={26} />
        <span className="font-display italic text-2xl leading-none text-ink">Reading Room</span>
      </div>

      {/* Permanent, always in the same place regardless of what's open below it. */}
      <div className="px-3 pb-3">
        <NavLink
          to="/chat"
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

        {/* Chat sits last on purpose: its dropdown opens downward into empty
            space, so Documents/Notes/Memory/Search/Flashcards above it never
            shift position when the conversation list expands or collapses. */}
        <div className="mt-auto pt-1">
          <button
            type="button"
            onClick={() => setChatOpen((open) => !open)}
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
              {CONVERSATIONS.map((c) => (
                <NavLink
                  key={c.id}
                  to={`/chat/${c.id}`}
                  className={({ isActive }) =>
                    `block truncate rounded-tab py-1.5 pl-2 pr-2 text-xs transition-colors ${
                      isActive ? 'bg-paper text-ink font-medium' : 'text-ink-soft hover:text-ink'
                    }`
                  }
                >
                  {c.title}
                </NavLink>
              ))}
            </div>
          )}
        </div>
      </nav>

      <div className="border-t border-mist px-5 py-4 font-mono text-[11px] text-ink-soft">
        v0.1
      </div>
    </aside>
  )
}