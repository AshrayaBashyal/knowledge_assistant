import { apiClient } from '../lib/apiClient'

export function fetchNotes() {
  return apiClient.get('/api/notes/')
}

export function fetchNote(id) {
  return apiClient.get(`/api/notes/${id}/`)
}

export function createNote({ title, content }) {
  return apiClient.post('/api/notes/', { title, content })
}

export function updateNote(id, { title, content }) {
  return apiClient.patch(`/api/notes/${id}/`, { title, content })
}

export function deleteNote(id) {
  return apiClient.delete(`/api/notes/${id}/`)
}