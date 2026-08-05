import { apiClient } from '../lib/apiClient'
import { setAccessToken, clearTokens } from '../lib/tokens'
import { getRefreshRequestPayload, persistRefreshToken, hasPossibleSession } from '../lib/refreshTokenStrategy'

export async function register({ email, password, fullName }) {
  return apiClient.post(
    '/api/accounts/register/',
    { email, password, full_name: fullName || undefined },
    { skipAuth: true },
  )
}

export async function login({ email, password }) {
  const data = await apiClient.post('/api/accounts/login/', { email, password }, { skipAuth: true })
  setAccessToken(data.access)
  persistRefreshToken(data.refresh)
  return data
}

export async function logout() {
  const { body, fetchOptions } = getRefreshRequestPayload()
  try {
    await apiClient.post('/api/accounts/logout/', body, fetchOptions)
  } catch {
    // Blacklisting server-side is best-effort - even if this call fails
    // (token already expired, network hiccup, etc.) we still want the
    // user logged out locally.
  } finally {
    clearTokens()
  }
}

/**
 * Exchanges the refresh token for a new access token (and, per the
 * backend's rotation policy, a new refresh token every time). Returns
 * true/false rather than throwing, since callers just need to know
 * whether the session could be restored.
 */
export async function refreshAccessToken() {
  const { body, fetchOptions } = getRefreshRequestPayload()

  try {
    const data = await apiClient.post('/api/accounts/login/refresh/', body, {
      skipAuth: true,
      ...fetchOptions,
    })
    setAccessToken(data.access)
    persistRefreshToken(data.refresh)
    return true
  } catch {
    clearTokens()
    return false
  }
}

export function fetchCurrentUser() {
  return apiClient.get('/api/accounts/me/')
}

// Re-exported so AuthContext can decide whether attempting a refresh on
// app start is even worth it, without importing the strategy file itself.
export { hasPossibleSession }