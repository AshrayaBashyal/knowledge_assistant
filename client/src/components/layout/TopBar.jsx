import { SignOut, UserCircle } from '@phosphor-icons/react'
import { useAuth } from '../../lib/AuthContext'

export default function TopBar({ title }) {
  const { user, logout } = useAuth()

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-mist px-8">
      <h1 className="font-display italic text-3xl text-ink">{title}</h1>
      <div className="flex items-center gap-4 font-mono text-xs text-ink-soft">
        <span className="flex items-center gap-2">
          <UserCircle size={20} />
          {user?.email ?? 'not signed in'}
        </span>
        {user && (
          <button
            onClick={logout}
            className="flex items-center gap-1.5 rounded-tab px-2 py-1 transition-colors hover:text-crimson"
            title="Sign out"
          >
            <SignOut size={16} />
            Sign out
          </button>
        )}
      </div>
    </header>
  )
}