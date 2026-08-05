// ── Refresh token strategy — isolated on purpose ──
//
// Today the backend returns the refresh token in the JSON body and expects
// it back in the JSON body of /login/refresh/ and /logout/. When it later
// switches to setting the refresh token as an httpOnly cookie, the browser
// will handle storing and sending it automatically - the app won't be able
// to read it at all, and won't need to.
//
// Every other file (apiClient, the future auth service, components) talks
// to the refresh token only through the functions below, never through
// localStorage directly. That means switching strategies later should mean
// editing ONLY this file:
//   - getRefreshRequestPayload(): stop reading from storage, return an
//     empty body + { credentials: 'include' } so the cookie rides along
//     automatically.
//   - persistRefreshToken(): becomes a no-op, since the server sets the
//     cookie itself via Set-Cookie.
//   - clearRefreshToken(): becomes a no-op or calls a dedicated
//     "clear cookie" endpoint if the backend adds one.
//   - hasPossibleSession(): under a cookie strategy we can't check
//     synchronously, so this should just return true and let the actual
//     refresh call on app start succeed or fail.

const REFRESH_TOKEN_KEY = 'reading_room_refresh_token'

/**
 * Body + fetch options to send with a POST /login/refresh/ (or /logout/)
 * request under the CURRENT (localStorage) strategy.
 */
export function getRefreshRequestPayload() {
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY)
  return {
    body: refresh ? { refresh } : {},
    fetchOptions: {},
  }
}

/**
 * Call after any successful response that includes a (possibly rotated)
 * refresh token - login, and every /login/refresh/ call.
 */
export function persistRefreshToken(token) {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}

export function clearRefreshToken() {
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

/**
 * Cheap, synchronous "might the user have a session worth restoring?"
 * check to decide whether it's worth attempting a refresh on app start.
 */
export function hasPossibleSession() {
  return Boolean(localStorage.getItem(REFRESH_TOKEN_KEY))
}