// Every backend error - validation, 404, 401, 429, 500 - comes back as
// {"detail": "..."} or, for validation errors, {"detail": {field: [msgs]}}.
// This class normalizes both shapes so callers don't need to know which
// one they got.
export class ApiError extends Error {
  constructor(status, detail) {
    const message = typeof detail === 'string' ? detail : 'Request failed'
    super(message)
    this.name = 'ApiError'
    this.status = status
    // fieldErrors is populated only when `detail` was an object keyed by
    // field name, e.g. {"email": ["This field is required."]}
    this.fieldErrors = typeof detail === 'object' && detail !== null ? detail : null
  }

  get isRateLimited() {
    return this.status === 429
  }

  get isUnauthorized() {
    return this.status === 401
  }
}