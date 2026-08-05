import { Outlet } from 'react-router-dom'
import Logo from '../Logo'

export default function AuthLayout() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-paper-dim px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center justify-center gap-2.5">
          <Logo size={30} />
          <span className="font-display italic text-3xl leading-none text-ink">Reading Room</span>
        </div>
        <Outlet />
      </div>
    </div>
  )
}