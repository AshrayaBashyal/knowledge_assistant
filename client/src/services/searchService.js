import { apiClient } from '../lib/apiClient'

export function search(query) {
  if (!query.trim()) return Promise.resolve({ results: [] })
  return apiClient.get(`/api/search/?q=${encodeURIComponent(query.trim())}`)
}