import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import Spinner from './ui/Spinner'

export default function ProtectedRoute() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'restoring') {
    return (
      <div className="flex h-screen items-center justify-center bg-paper">
        <Spinner size={28} className="text-ink-soft" />
      </div>
    )
  }

  if (status === 'unauthenticated') {
    // Remember where they were headed so login can send them back.
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}