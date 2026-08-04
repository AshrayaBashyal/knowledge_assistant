import { UserCircle } from '@phosphor-icons/react'

export default function TopBar({ title }) {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-mist px-8">
      <h1 className="font-display italic text-3xl text-ink">{title}</h1>
      <div className="flex items-center gap-2 font-mono text-xs text-ink-soft">
        <UserCircle size={20} />
        <span>not signed in</span>
      </div>
    </header>
  )
}