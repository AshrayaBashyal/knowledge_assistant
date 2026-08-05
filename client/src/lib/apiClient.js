import { API_BASE_URL } from './env'
import { getAccessToken } from './tokens'
import { ApiError } from './ApiError'

// Registered by the auth layer later. When a request comes back 401,
// apiClient calls this (if set) to give auth a chance to refresh the access
// token and retry, without apiClient needing to know anything about how
// auth or refresh actually works.
let unauthorizedHandler = null

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler
}

async function parseErrorBody(response) {
  try {
    const body = await response.json()
    return body?.detail ?? 'Request failed'
  } catch {
    return 'Request failed'
  }
}

/**
 * Low-level request function. Handles JSON bodies, auth headers, and
 * normalizing errors into ApiError. Feature-specific endpoint calls
 * (login, documents, etc.) are built on top of this in later stages.
 */
async function request(path, { method = 'GET', body, isFormData = false, skipAuth = false, retriedAfterRefresh = false } = {}) {
  const headers = {}
  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  const accessToken = getAccessToken()
  if (!skipAuth && accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : isFormData ? body : JSON.stringify(body),
  })

  if (response.status === 401 && !skipAuth && !retriedAfterRefresh && unauthorizedHandler) {
    const refreshed = await unauthorizedHandler()
    if (refreshed) {
      return request(path, { method, body, isFormData, skipAuth, retriedAfterRefresh: true })
    }
  }

  if (!response.ok) {
    const detail = await parseErrorBody(response)
    throw new ApiError(response.status, detail)
  }

  // 204/205 responses have no body
  if (response.status === 204 || response.status === 205) {
    return null
  }

  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    return response.json()
  }
  return response
}

export const apiClient = {
  get: (path, opts) => request(path, { ...opts, method: 'GET' }),
  post: (path, body, opts) => request(path, { ...opts, method: 'POST', body }),
  patch: (path, body, opts) => request(path, { ...opts, method: 'PATCH', body }),
  delete: (path, opts) => request(path, { ...opts, method: 'DELETE' }),
  postForm: (path, formData, opts) => request(path, { ...opts, method: 'POST', body: formData, isFormData: true }),
  // Raw fetch for cases that need the Response object directly (file
  // download, SSE streaming) rather than a parsed JSON body.
  raw: (path, options = {}) => {
    const headers = { ...(options.headers || {}) }
    const accessToken = getAccessToken()
    if (!options.skipAuth && accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`
    }
    return fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  },
}