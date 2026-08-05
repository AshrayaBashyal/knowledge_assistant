import { apiClient } from '../lib/apiClient'

export function fetchDocuments() {
  return apiClient.get('/api/documents/')
}

export function fetchDocument(id) {
  return apiClient.get(`/api/documents/${id}/`)
}

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  return apiClient.postForm('/api/documents/', formData)
}

export function deleteDocument(id) {
  return apiClient.delete(`/api/documents/${id}/`)
}

// Returns a raw Response so the caller can stream the bytes directly into
// a temporary object URL for download, without loading the whole file into
// memory as a JS string.
export function downloadDocument(id) {
  return apiClient.raw(`/api/documents/${id}/download/`)
}