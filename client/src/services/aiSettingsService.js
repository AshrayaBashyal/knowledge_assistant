import { apiClient } from '../lib/apiClient'

export async function fetchAiSettings() {
  return apiClient.get('/api/accounts/ai-settings/')
}

export async function updateAiSettings(data) {
  return apiClient.post('/api/accounts/ai-settings/', data)
}

export async function resetAiSettings() {
  return apiClient.delete('/api/accounts/ai-settings/')
}

export async function validateApiKey({ provider, api_key, model }) {
  return apiClient.post('/api/accounts/ai-settings/validate/', {
    provider,
    api_key,
    model,
  })
}
