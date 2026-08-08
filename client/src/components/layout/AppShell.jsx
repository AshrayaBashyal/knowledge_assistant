import { useEffect } from 'react'
import { Outlet, useMatches } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import { useState } from 'react'

export default function AppShell() {
  const matches = useMatches()
  const current = [...matches].reverse().find((m) => m.handle?.title)
  const title = current?.handle?.title ?? 'Reading Room'
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    document.title = title === 'Reading Room' ? 'Reading Room' : `${title} — Reading Room`
  }, [title])

  return (
    <div className="flex h-screen bg-paper">
      {/* Mobile sidebar overlay backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-ink/20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar - fixed on mobile, static on desktop */}
      <div className={`
        fixed inset-y-0 left-0 z-40 lg:static lg:z-auto
        transform transition-transform duration-200 ease-in-out lg:transform-none
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <Sidebar onNavClick={() => setSidebarOpen(false)} />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={title} onMenuClick={() => setSidebarOpen((o) => !o)} />
        <main className="flex-1 overflow-y-auto px-4 py-4 sm:px-6 sm:py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}