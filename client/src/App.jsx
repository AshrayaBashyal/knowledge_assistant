import { RouterProvider } from 'react-router-dom'
import { router } from './routes/router'
import { ToastProvider } from './lib/ToastContext'
import { AuthProvider } from './lib/AuthContext'

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </ToastProvider>
  )
}