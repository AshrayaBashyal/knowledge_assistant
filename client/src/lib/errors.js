import { ApiError } from './ApiError'

// Turns whatever came out of a catch block into a single string suitable
// for a toast or inline alert. Field-validation errors get flattened into
// one readable line rather than requiring every call site to know the
// backend's {field: [messages]} shape.
export function getErrorMessage(error) {
  if (error instanceof ApiError) {
    if (error.isRateLimited) {
      return error.message
    }
    if (error.fieldErrors) {
      return Object.entries(error.fieldErrors)
        .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
        .join(' ')
    }
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Something went wrong. Please try again.'
}