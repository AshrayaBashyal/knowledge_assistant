import { apiClient } from '../lib/apiClient'

export function fetchConversations() {
  return apiClient.get('/api/chat/conversations/')
}

export function fetchConversation(id) {
  return apiClient.get(`/api/chat/conversations/${id}/`)
}

export function createConversation(title) {
  return apiClient.post('/api/chat/conversations/', { title })
}

export function renameConversation(id, title) {
  return apiClient.patch(`/api/chat/conversations/${id}/`, { title })
}

export function deleteConversation(id) {
  return apiClient.delete(`/api/chat/conversations/${id}/`)
}

// Returns a raw Response so the caller can hand the body's ReadableStream
// to sse.js for frame-by-frame reading. We don't use apiClient.post() here
// because that awaits .json() - we need the raw response instead.
export function streamChat({ message, conversationId }) {
  return apiClient.raw('/api/chat/stream/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      ...(conversationId ? { conversation_id: conversationId } : {}),
    }),
  })
}