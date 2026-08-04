import { Outlet, useMatches } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

export default function AppShell() {
  const matches = useMatches()
  const current = [...matches].reverse().find((m) => m.handle?.title)
  const title = current?.handle?.title ?? 'Reading Room'

  return (
    <div className="flex h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={title} />
        <main className="flex-1 overflow-y-auto px-8 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}