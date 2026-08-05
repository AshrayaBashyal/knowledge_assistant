import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { setUnauthorizedHandler } from './apiClient'
import * as authService from '../services/authService'

const AuthContext = createContext(null)

// 'restoring' -> checking for an existing session on app start
// 'authenticated' | 'unauthenticated' -> settled states
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('restoring')

  const loadCurrentUser = useCallback(async () => {
    const me = await authService.fetchCurrentUser()
    setUser(me)
    setStatus('authenticated')
  }, [])

  // Session restoration: on a fresh page load there's no access token in
  // memory, only (possibly) a refresh token in storage. If one might
  // exist, trade it for a new access token and fetch the user; otherwise
  // skip straight to unauthenticated without a wasted network call.
  useEffect(() => {
    let cancelled = false

    async function restore() {
      if (!authService.hasPossibleSession()) {
        setStatus('unauthenticated')
        return
      }
      const refreshed = await authService.refreshAccessToken()
      if (cancelled) return
      if (!refreshed) {
        setStatus('unauthenticated')
        return
      }
      try {
        await loadCurrentUser()
      } catch {
        if (!cancelled) setStatus('unauthenticated')
      }
    }

    restore()
    return () => {
      cancelled = true
    }
  }, [loadCurrentUser])

  // Give apiClient a way to attempt a refresh-and-retry on any 401,
  // without apiClient knowing anything about auth itself.
  useEffect(() => {
    setUnauthorizedHandler(async () => {
      const refreshed = await authService.refreshAccessToken()
      if (!refreshed) {
        setUser(null)
        setStatus('unauthenticated')
      }
      return refreshed
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const login = useCallback(async (credentials) => {
    await authService.login(credentials)
    await loadCurrentUser()
  }, [loadCurrentUser])

  const register = useCallback(async (details) => {
    await authService.register(details)
  }, [])

  const logout = useCallback(async () => {
    await authService.logout()
    setUser(null)
    setStatus('unauthenticated')
  }, [])

  return (
    <AuthContext.Provider value={{ user, status, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}