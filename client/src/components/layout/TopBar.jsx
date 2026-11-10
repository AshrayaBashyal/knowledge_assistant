import { useState } from 'react'
import { SignOut, UserCircle, List, Cpu, ShieldCheck } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../lib/AuthContext'
import AiSettingsModal from '../AiSettingsModal'

export default function TopBar({ title, onMenuClick }) {
  const { user, logout } = useAuth()
  const [aiSettingsOpen, setAiSettingsOpen] = useState(false)

  return (
    <>
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-mist px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          {/* Hamburger only visible on mobile */}
          <button
            onClick={onMenuClick}
            className="rounded-tab p-1.5 text-ink-soft hover:text-ink lg:hidden"
            aria-label="Toggle navigation"
          >
            <List size={20} />
          </button>
          <h1 className="font-display italic text-2xl leading-none text-ink sm:text-3xl">{title}</h1>
        </div>

        <div className="flex items-center gap-2.5 font-mono text-xs text-ink-soft">
          {/* AI Settings button in top bar */}
          <button
            type="button"
            onClick={() => setAiSettingsOpen(true)}
            className="flex items-center gap-1.5 rounded-tab border border-mist bg-paper-dim px-2.5 py-1 text-ink-soft hover:text-ink hover:bg-paper transition-colors"
            title="Configure AI Models & API Keys"
          >
            <Cpu size={15} className="text-brass" />
            <span className="hidden sm:inline">AI Keys</span>
          </button>

          {/* Admin badge link */}
          {user?.is_staff && (
            <Link
              to="/admin"
              className="flex items-center gap-1 rounded-tab border border-brass/40 bg-brass/10 px-2 py-1 text-ink hover:bg-brass/20 transition-colors"
              title="Admin & Metrics Dashboard"
            >
              <ShieldCheck size={15} className="text-brass" />
              <span className="hidden sm:inline">Admin</span>
            </Link>
          )}

          <span className="hidden items-center gap-1.5 sm:flex ml-1">
            <UserCircle size={18} />
            <span className="max-w-[150px] truncate">{user?.email ?? 'not signed in'}</span>
          </span>

          {user && (
            <button
              onClick={logout}
              className="flex items-center gap-1.5 rounded-tab px-2 py-1 transition-colors hover:text-crimson ml-1"
              title="Sign out"
            >
              <SignOut size={16} />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          )}
        </div>
      </header>

      <AiSettingsModal
        isOpen={aiSettingsOpen}
        onClose={() => setAiSettingsOpen(false)}
      />
    </>
  )
}
