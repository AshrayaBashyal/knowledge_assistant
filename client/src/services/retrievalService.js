import { apiClient } from '../lib/apiClient'

export function triggerDocumentIndex(id) {
  return apiClient.post(`/api/retrieval/documents/${id}/index/`, {})
}

export function fetchDocumentIndexStatus(id) {
  return apiClient.get(`/api/retrieval/documents/${id}/index/`)
}

export function triggerNoteIndex(id) {
  return apiClient.post(`/api/retrieval/notes/${id}/index/`, {})
}

export function fetchNoteIndexStatus(id) {
  return apiClient.get(`/api/retrieval/notes/${id}/index/`)
}