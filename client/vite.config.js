import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Frontend calls relative paths like /api/accounts/login/ - this proxy
// forwards those to the Django backend during dev so we never deal with
// CORS locally, and switching backend hosts later is a one-line change.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})