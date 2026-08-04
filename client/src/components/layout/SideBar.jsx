import { NavLink } from 'react-router-dom'
import { ChatCircleDots, FileText, NotePencil, Brain, MagnifyingGlass, Cards,} from '@phosphor-icons/react'
import Logo from '../Logo'

const NAV_ITEMS = [
  { to: '/', label: 'Chat', icon: ChatCircleDots, end: true },
  { to: '/documents', label: 'Documents', icon: FileText },
  { to: '/notes', label: 'Notes', icon: NotePencil },
  { to: '/memory', label: 'Memory', icon: Brain },
  { to: '/search', label: 'Search', icon: MagnifyingGlass },
  { to: '/flashcards', label: 'Flashcards', icon: Cards },
]

export default function Sidebar() {
  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r border-mist bg-paper-dim">
      <div className="flex items-center gap-2.5 px-5 py-6">
        <Logo size={26} />
        <span className="font-display italic text-2xl leading-none text-ink">Reading Room</span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `group relative flex items-center gap-3 rounded-tab py-2.5 pl-4 pr-3 text-sm font-body transition-colors ${
                isActive ? 'text-ink' : 'text-ink-soft hover:text-ink'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {/* the "pulled out" catalog tab standing in for a highlight */}
                <span
                  aria-hidden="true"
                  className={`absolute -left-3 top-1/2 h-5 w-1.5 -translate-y-1/2 rounded-tab-sm transition-opacity ${
                    isActive ? 'bg-brass opacity-100' : 'opacity-0'
                  }`}
                />
                <Icon size={19} weight={isActive ? 'duotone' : 'regular'} />
                <span className={isActive ? 'font-medium' : ''}>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-mist px-5 py-4 font-mono text-[11px] text-ink-soft">
        v0.1 — stage 1
      </div>
    </aside>
  )
}