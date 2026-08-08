import { SignOut, UserCircle, List } from '@phosphor-icons/react'
import { useAuth } from '../../lib/AuthContext'

export default function TopBar({ title, onMenuClick }) {
  const { user, logout } = useAuth()

  return (
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

      <div className="flex items-center gap-3 font-mono text-xs text-ink-soft">
        <span className="hidden items-center gap-1.5 sm:flex">
          <UserCircle size={18} />
          <span className="max-w-[160px] truncate">{user?.email ?? 'not signed in'}</span>
        </span>
        {user && (
          <button
            onClick={logout}
            className="flex items-center gap-1.5 rounded-tab px-2 py-1 transition-colors hover:text-crimson"
            title="Sign out"
          >
            <SignOut size={16} />
            <span className="hidden sm:inline">Sign out</span>
          </button>
        )}
      </div>
    </header>
  )
}