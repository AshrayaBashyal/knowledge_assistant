import { apiClient } from '../lib/apiClient'

export function generateFlashcards({ sourceType, sourceId, count }) {
  return apiClient.post('/api/flashcards/generate/', {
    source_type: sourceType,
    source_id: sourceId,
    count: count ?? 10,
  })
}

export function fetchFlashcardSets() {
  return apiClient.get('/api/flashcards/sets/')
}

export function fetchFlashcardSet(id) {
  return apiClient.get(`/api/flashcards/sets/${id}/`)
}

export function deleteFlashcardSet(id) {
  return apiClient.delete(`/api/flashcards/sets/${id}/`)
}

export function updateFlashcard(cardId, { question, answer, difficulty, category }) {
  return apiClient.patch(`/api/flashcards/${cardId}/`, { question, answer, difficulty, category })
}

export function deleteFlashcard(cardId) {
  return apiClient.delete(`/api/flashcards/${cardId}/`)
}