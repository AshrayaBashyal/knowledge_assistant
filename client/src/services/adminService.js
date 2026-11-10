import { apiClient } from '../lib/apiClient'

export async function fetchAdminMetrics() {
  return apiClient.get('/api/admin/metrics/')
}

export async function fetchAdminLogs({ level = '', search = '', limit = 100 } = {}) {
  const params = new URLSearchParams()
  if (level) params.set('level', level)
  if (search) params.set('search', search)
  if (limit) params.set('limit', limit)

  const query = params.toString() ? `?${params.toString()}` : ''
  return apiClient.get(`/api/admin/logs/${query}`)
}
