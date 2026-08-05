// Access token strategy - lives only in memory (a module-level variable),
// never localStorage, so it can't be scraped by a stray XSS'd script and
// isn't affected by whatever the refresh token strategy is doing. This
// part doesn't change when the backend switches to httpOnly cookies for
// the refresh token, so it stays separate from refreshTokenStrategy.js.

import { clearRefreshToken } from './refreshTokenStrategy'

let accessToken = null

export function getAccessToken() {
  return accessToken
}

export function setAccessToken(token) {
  accessToken = token
}

// Convenience for logout / failed-refresh cleanup - clears both tokens
// without callers needing to know about refreshTokenStrategy.js directly.
export function clearTokens() {
  accessToken = null
  clearRefreshToken()
}