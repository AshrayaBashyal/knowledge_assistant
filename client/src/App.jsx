import { RouterProvider } from 'react-router-dom'
import { router } from './routes/router'
import { ToastProvider } from './lib/ToastContext'

export default function App() {
  return (
    <ToastProvider>
      <RouterProvider router={router} />
    </ToastProvider>
  )
}