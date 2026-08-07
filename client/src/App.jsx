import { RouterProvider } from 'react-router-dom'
import { router } from './routes/router'
import { ToastProvider } from './lib/ToastContext'
import { AuthProvider } from './lib/AuthContext'
import { ConversationsProvider } from './lib/ConversationsContext'

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <ConversationsProvider>
          <RouterProvider router={router} />
        </ConversationsProvider>
      </AuthProvider>
    </ToastProvider>
  )
}