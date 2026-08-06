import { apiClient } from '../lib/apiClient'

export function fetchMemories() {
  return apiClient.get('/api/memory/')
}

export function createMemory({ content }) {
  return apiClient.post('/api/memory/', { content })
}

export function updateMemory(id, { content }) {
  return apiClient.patch(`/api/memory/${id}/`, { content })
}

export function deleteMemory(id) {
  return apiClient.delete(`/api/memory/${id}/`)
}